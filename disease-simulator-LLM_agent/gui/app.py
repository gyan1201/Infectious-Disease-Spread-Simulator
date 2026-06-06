"""
Disease Simulator GUI — Streamlit front-end for vanilla-0.1-jar-with-dependencies.jar.

Tab 1  Configure & Run  — edit parameters, pick files, launch Java simulation.
Tab 2  Results           — choropleth map + SEIR curves with a per-day slider.
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Paths (all relative to disease-simulator-main/)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
JAR_PATH = BASE_DIR / "target" / "vanilla-0.1-jar-with-dependencies.jar"
EXAMPLES_DIR = BASE_DIR / "examples"
LOGS_DIR = BASE_DIR / "logs"

STEPS_PER_DAY = 288  # 5 min/step × 288 = 1 day
PID_FILE = BASE_DIR / ".sim_pid"  # tracks running Java process across refreshes
SIM_STATE_FILE = BASE_DIR / ".sim_state.json"  # pid + log prefix + start time

CITY_PROPS = {
    "Atlanta": str(EXAMPLES_DIR / "atlanta.properties"),
    "San Francisco": str(EXAMPLES_DIR / "sanfran.properties"),
}

SCENARIO_BIAS = {
    "S1 – Independent": str(EXAMPLES_DIR / "bias.llm.properties"),
    "S2 – Household influence": str(EXAMPLES_DIR / "bias.llm.S2.properties"),
    "S3 – Message framing": str(EXAMPLES_DIR / "bias.llm.S3.properties"),
}

GUI_DIR = Path(__file__).parent
REGION_GEOJSON = {
    "Atlanta": str(GUI_DIR / "atlanta_regions.geojson"),
    "San Francisco": str(GUI_DIR / "san-fran_regions.geojson"),
}

SEIR_COLORS = {
    "Susceptible": "#3498db",
    "Exposed": "#f39c12",
    "Infectious": "#e74c3c",
    "Recovered": "#2ecc71",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_properties(path: str) -> dict:
    """Read a .properties file into an ordered dict."""
    props = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                props[k.strip()] = v.strip()
    return props


def write_properties(path: str, props: dict):
    """Write a dict back to a .properties file."""
    with open(path, "w") as f:
        for k, v in props.items():
            f.write(f"{k} = {v}\n")


def parse_disease_reports(tsv_path: str) -> pd.DataFrame:
    """
    Parse DiseaseReports.tsv into a tidy DataFrame.

    Columns: step, agentId, regionId, diseaseStatus, reported
    """
    rows = []
    pattern = re.compile(r"\[([^\]]+)\]")
    with open(tsv_path, encoding="utf-8") as f:
        try:
            next(f)  # skip header
        except StopIteration:
            return pd.DataFrame(columns=["step", "agentId", "regionId", "diseaseStatus", "reported", "day"])
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            try:
                step = int(parts[0])
                agent_id = int(parts[1])
            except ValueError:
                continue
            m = pattern.search(parts[2])
            if not m:
                continue
            fields = m.group(1).split(",")
            region_id = int(fields[0]) if fields[0].strip().lstrip("-").isdigit() else None
            disease_status = fields[1].strip() if len(fields) > 1 else ""
            reported = fields[7].strip().lower() == "true" if len(fields) > 7 else False
            rows.append(
                {
                    "step": step,
                    "agentId": agent_id,
                    "regionId": region_id,
                    "diseaseStatus": disease_status,
                    "reported": reported,
                }
            )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["day"] = df["step"] // STEPS_PER_DAY
    return df


@st.cache_data(show_spinner=False)
def load_disease_reports(tsv_path: str) -> pd.DataFrame:
    return parse_disease_reports(tsv_path)


@st.cache_data(show_spinner=False)
def load_geodata(city: str) -> dict:
    """Load pre-converted GeoJSON for a city. Returns raw dict or None."""
    path = REGION_GEOJSON.get(city)
    if not path or not Path(path).exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _map_center(geojson: dict, default: list) -> list:
    """Compute lat/lon center from GeoJSON feature bounding boxes."""
    lats, lons = [], []
    for feature in geojson["features"]:
        coords = feature["geometry"].get("coordinates", [])
        for polygon in (coords if feature["geometry"]["type"] == "MultiPolygon" else [coords]):
            for ring in polygon:
                for lon, lat in ring:
                    lats.append(lat)
                    lons.append(lon)
    return [sum(lats) / len(lats), sum(lons) / len(lons)] if lats else default


_GRADIENTS = {
    "YlOrRd": "linear-gradient(to right, #ffffcc, #fd8d3c, #bd0026)",
    "Blues":  "linear-gradient(to right, #eff3ff, #6baed6, #084594)",
}


def _add_custom_legend(
    m: folium.Map,
    choropleth: folium.Choropleth,
    title: str,
    min_val: float,
    max_val: float,
    color_scheme: str,
) -> None:
    """
    Remove branca's built-in SVG legend (transparent background, text overlaps bar)
    and replace it with a clean HTML legend: title above the bar, solid white background.
    """
    # Drop the auto-generated branca colormap child so it doesn't render
    for key in list(choropleth._children.keys()):
        if key.startswith("color_map"):
            del choropleth._children[key]
            break

    gradient = _GRADIENTS.get(color_scheme, _GRADIENTS["YlOrRd"])
    min_label = f"{min_val:.1f}" if isinstance(min_val, float) else str(min_val)
    max_label = f"{max_val:.1f}" if isinstance(max_val, float) else str(max_val)

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 16px; left: 16px;
        z-index: 1000;
        background: white;
        padding: 9px 13px 8px 13px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.30);
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
        min-width: 190px;
    ">
        <div style="font-weight: 600; margin-bottom: 6px; color: #222;">{title}</div>
        <div style="
            width: 170px; height: 13px;
            background: {gradient};
            border-radius: 2px;
            border: 1px solid #ccc;
        "></div>
        <div style="
            display: flex; justify-content: space-between;
            width: 170px; margin-top: 3px;
            font-size: 10px; color: #555;
        ">
            <span>{min_label}</span><span>{max_label}</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def build_reporting_map(geojson: dict, df: pd.DataFrame, selected_day: int):
    """
    Choropleth of cumulative reporting rate per region up to selected_day.
    Rate = (agents who ever reported) / (agents ever infected) × 100.
    """
    cumulative_df = df[df["day"] <= selected_day]

    # Agents who were ever infected (Infectious or Recovered) up to this day
    ever_infected = (
        cumulative_df[cumulative_df["diseaseStatus"].isin(["Infectious", "Recovered"])]
        .groupby(["regionId", "agentId"])
        .size()
        .reset_index()[["regionId", "agentId"]]
    )
    ever_infected_count = ever_infected.groupby("regionId")["agentId"].nunique()

    # Agents who ever reported (reported=True at any row) up to this day
    ever_reported = (
        cumulative_df[cumulative_df["reported"]]
        .groupby(["regionId", "agentId"])
        .size()
        .reset_index()[["regionId", "agentId"]]
    )
    ever_reported_count = ever_reported.groupby("regionId")["agentId"].nunique()

    # Reporting rate per region (0–100 %)
    rate = (ever_reported_count / ever_infected_count * 100).fillna(0).rename("ReportingRate")
    rate_df = rate.reset_index().rename(columns={"regionId": "id"})

    # Inject into GeoJSON properties for tooltip
    rate_by_id = rate_df.set_index("id")["ReportingRate"]
    infected_by_id = ever_infected_count
    reported_by_id = ever_reported_count
    for feature in geojson["features"]:
        rid = feature["properties"].get("id")
        feature["properties"]["ReportingRate"] = round(float(rate_by_id.get(rid, 0.0)), 1)
        feature["properties"]["EverInfected"] = int(infected_by_id.get(rid, 0))
        feature["properties"]["EverReported"] = int(reported_by_id.get(rid, 0))

    center = _map_center(geojson, [33.75, -84.39])
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")

    cp_report = folium.Choropleth(
        geo_data=geojson,
        data=rate_df,
        columns=["id", "ReportingRate"],
        key_on="feature.properties.id",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.3,
        nan_fill_color="lightgray",
    )
    cp_report.add_to(m)
    _add_custom_legend(
        m, cp_report,
        title=f"Reporting rate % (Day 0–{selected_day})",
        min_val=0.0,
        max_val=100.0,
        color_scheme="YlOrRd",
    )

    folium.GeoJson(
        geojson,
        tooltip=folium.GeoJsonTooltip(
            fields=["id", "ReportingRate", "EverReported", "EverInfected"],
            aliases=["Region", "Reporting rate (%)", "Ever reported", "Ever infected"],
        ),
        style_function=lambda x: {"fillOpacity": 0, "weight": 0},
    ).add_to(m)

    return m


def build_choropleth(geojson: dict, day_df: pd.DataFrame, metric: str, day: int):
    """Return a folium.Map with a choropleth layer for the given day."""
    # Aggregate per region
    counts = (
        day_df.groupby(["regionId", "diseaseStatus"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in ["Susceptible", "Exposed", "Infectious", "Recovered"]:
        if col not in counts.columns:
            counts[col] = 0

    # Inject SEIR counts into GeoJSON feature properties
    counts_by_id = counts.set_index("regionId")
    for feature in geojson["features"]:
        rid = feature["properties"].get("id")
        for col in ["Susceptible", "Exposed", "Infectious", "Recovered"]:
            feature["properties"][col] = int(counts_by_id.loc[rid, col]) if rid in counts_by_id.index else 0

    center = _map_center(geojson, [33.75, -84.39])
    m = folium.Map(location=center, zoom_start=12, tiles="CartoDB positron")

    # Build data series for choropleth
    data_rows = [
        (f["properties"]["id"], f["properties"].get(metric, 0))
        for f in geojson["features"]
    ]
    data_df = pd.DataFrame(data_rows, columns=["id", metric])

    color_scheme = "YlOrRd" if metric == "Infectious" else "Blues"
    choropleth = folium.Choropleth(
        geo_data=geojson,
        data=data_df,
        columns=["id", metric],
        key_on="feature.properties.id",
        fill_color=color_scheme,
        fill_opacity=0.7,
        line_opacity=0.3,
        nan_fill_color="lightgray",
    )
    choropleth.add_to(m)
    max_val = int(data_df[metric].max()) if not data_df.empty else 0
    _add_custom_legend(
        m, choropleth,
        title=f"{metric} agents — Day {day}",
        min_val=0,
        max_val=max_val,
        color_scheme=color_scheme,
    )

    folium.GeoJson(
        geojson,
        tooltip=folium.GeoJsonTooltip(
            fields=["id", "Susceptible", "Exposed", "Infectious", "Recovered"],
            aliases=["Region", "Susceptible", "Exposed", "Infectious", "Recovered"],
        ),
        style_function=lambda x: {"fillOpacity": 0, "weight": 0},
    ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Disease Simulator",
    page_icon="🦠",
    layout="wide",
)
st.title("Infectious Disease Spread Simulator")
st.caption("LLM Decision-Making Agent-Based Model")

# --- Global simulation status banner (visible on both tabs) ---
def _read_sim_state() -> dict | None:
    """Return state dict if a sim process is recorded and still alive, else None."""
    if not SIM_STATE_FILE.exists():
        return None
    try:
        state = json.loads(SIM_STATE_FILE.read_text())
        pid = state.get("pid")
        if pid is None:
            return None
        # Check the process is actually still running
        os.kill(pid, 0)  # signal 0 = existence check only, raises if gone
        return state
    except (json.JSONDecodeError, ProcessLookupError, PermissionError, OSError):
        SIM_STATE_FILE.unlink(missing_ok=True)
        return None

sim_state = _read_sim_state()
if sim_state:
    st.warning(
        f"**Simulation running** — PID `{sim_state['pid']}` | "
        f"Log folder: `logs/{sim_state['log_prefix']}/` | "
        f"Started: {sim_state['started']} | "
        f"{sim_state['city']} · {sim_state['scenario']} · {sim_state['reporting_model']} · "
        f"{sim_state['num_agents']} agents · {sim_state['sim_days']} days"
    )

tab_run, tab_results = st.tabs(["Configure & Run", "Results"])

# ===========================================================================
# TAB 1 — Configure & Run
# ===========================================================================
with tab_run:
    st.subheader("Simulation Configuration")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Scenario**")
        city = st.selectbox("City", list(CITY_PROPS.keys()))
        reporting_model = st.radio("Reporting model", ["LLM", "LR"], horizontal=True)
        scenario = st.selectbox(
            "Scenario (LLM only)",
            list(SCENARIO_BIAS.keys()),
            disabled=(reporting_model == "LR"),
        )
        decision_bank = st.text_input(
            "Decision bank CSV (LLM only)",
            value=str(EXAMPLES_DIR / "llm.atl.csv"),
            disabled=(reporting_model == "LR"),
        )
        log_prefix = st.text_input("Output log prefix", value="gui-run")

    with col_right:
        st.markdown("**SEIR & Disease Parameters**")

        # Load defaults from the city .properties file
        default_props = read_properties(CITY_PROPS[city]) if Path(CITY_PROPS[city]).exists() else {}

        num_agents = st.number_input(
            "Number of agents",
            min_value=100,
            max_value=50000,
            value=int(default_props.get("numOfAgents", 2000)),
            step=100,
        )
        seed = st.number_input("Random seed", min_value=0, value=int(default_props.get("seed", 1)))
        init_infectious = st.slider(
            "Initial infectious (%)",
            min_value=1,
            max_value=20,
            value=int(default_props.get("initPercentInfectious", 1)),
        )
        prob_test = st.slider(
            "P(test positive | symptomatic)",
            min_value=0.0,
            max_value=1.0,
            value=float(default_props.get("probTestPositive", 0.05)),
            step=0.01,
            format="%.2f",
        )
        prob_clinical = st.slider(
            "P(clinical diagnosis)",
            min_value=0.0,
            max_value=1.0,
            value=float(default_props.get("probClinicalDiagnosis", 0.5)),
            step=0.01,
            format="%.2f",
        )
        sim_days = st.number_input(
            "Simulation duration (days)",
            min_value=1,
            max_value=365,
            value=90,
        )

    with st.expander("Advanced SEIR parameters", expanded=False):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            exposed_lasting = st.text_input(
                "Exposed duration range (days)",
                value=default_props.get("exposedLasting", "1-5"),
                help="e.g. 1-5  (min-max days in Exposed state)",
            )
            infectious_lasting = st.text_input(
                "Infectious duration range (days)",
                value=default_props.get("infectiousLasting", "5-8"),
                help="e.g. 5-8",
            )
        with adv_col2:
            recovered_lasting = st.text_input(
                "Recovered duration range (days)",
                value=default_props.get("recoveredLasting", "30-180"),
                help="e.g. 30-180",
            )
            spread_param = st.number_input(
                "Additional spread probability",
                min_value=0.0,
                max_value=1.0,
                value=float(default_props.get("additionalDiseaseSpreadingParam", 0.03)),
                step=0.005,
                format="%.3f",
                help="Extra per-contact infection probability",
            )

    st.divider()

    run_col, stop_col, info_col = st.columns([1, 1, 4])
    with run_col:
        run_clicked = st.button("Run Simulation", type="primary", use_container_width=True)
    with stop_col:
        stop_clicked = st.button("Stop", type="secondary", use_container_width=True)
    with info_col:
        st.info(f"Log folder: `logs/{log_prefix}/`  — select this name in the **Results** tab after the run.")

    # Stop button: kill the running process (survives page refresh via PID file)
    if stop_clicked:
        killed = False
        # Try in-memory handle first (same session, no refresh)
        proc_running = st.session_state.get("sim_proc")
        if proc_running and proc_running.poll() is None:
            proc_running.terminate()
            killed = True
        elif PID_FILE.exists():
            # Recover PID written at launch — works after a page refresh
            try:
                pid = int(PID_FILE.read_text().strip())
                os.kill(pid, 15)  # SIGTERM (signal 15); on Windows this calls TerminateProcess
                killed = True
            except (ProcessLookupError, PermissionError, ValueError):
                pass
            finally:
                PID_FILE.unlink(missing_ok=True)
        if killed:
            st.warning("Simulation process terminated.")
        else:
            st.warning("No simulation is currently running.")

    log_placeholder = st.empty()

    if run_clicked:
        if not JAR_PATH.exists():
            st.error(f"JAR not found: {JAR_PATH}\nRun `mvn ... assembly:single` first.")
        else:
            # Build a temp properties file with overrides
            base_props = read_properties(CITY_PROPS[city]) if Path(CITY_PROPS[city]).exists() else {}
            base_props["numOfAgents"] = str(num_agents)
            base_props["seed"] = str(seed)
            base_props["initPercentInfectious"] = str(init_infectious)
            base_props["probTestPositive"] = str(prob_test)
            base_props["probClinicalDiagnosis"] = str(prob_clinical)
            base_props["reportingModel"] = reporting_model
            base_props["exposedLasting"] = exposed_lasting
            base_props["infectiousLasting"] = infectious_lasting
            base_props["recoveredLasting"] = recovered_lasting
            base_props["additionalDiseaseSpreadingParam"] = str(spread_param)

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".properties", delete=False, dir=str(BASE_DIR)
            ) as tmp_props:
                write_properties(tmp_props.name, base_props)
                tmp_props_path = tmp_props.name

            bias_config = SCENARIO_BIAS[scenario]
            single_config = str(EXAMPLES_DIR / "bias.single.properties")
            # +2 ensures the last day boundary (step N*288) is fully crossed
            until_steps = sim_days * STEPS_PER_DAY + 2

            # Each -D flag must be a single list element (no spaces inside).
            # Passing as a list bypasses all shell parsing, which avoids the
            # Windows CMD/PowerShell bug that splits -Dlog4j2.xxx into two tokens.
            cmd = [
                "java",
                "-Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory",
                "-Dlog.rootDirectory=logs",
                f"-Dfile.prefix={log_prefix}",
                "-Dsimulation.test=bias",
                "-jar", str(JAR_PATH),
                "-configuration", tmp_props_path,
                "-bias.config", bias_config,
                "-bias.single.config", single_config,
                "-until", str(until_steps),
            ]
            if reporting_model == "LLM" and decision_bank:
                cmd += ["-decision.bank", decision_bank]

            st.session_state["last_log_prefix"] = log_prefix

            log_lines = []
            log_box = log_placeholder.empty()

            proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            PID_FILE.write_text(str(proc.pid))  # persist PID so Stop works after refresh
            SIM_STATE_FILE.write_text(json.dumps({
                "pid": proc.pid,
                "log_prefix": log_prefix,
                "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "city": city,
                "scenario": scenario,
                "reporting_model": reporting_model,
                "sim_days": sim_days,
                "num_agents": num_agents,
            }))
            st.session_state["sim_proc"] = proc
            for line in proc.stdout:
                log_lines.append(line.rstrip())
                log_box.code("\n".join(log_lines[-40:]))
            proc.wait()
            PID_FILE.unlink(missing_ok=True)
            SIM_STATE_FILE.unlink(missing_ok=True)  # clean up when done
            os.unlink(tmp_props_path)

            rc = proc.returncode
            if rc == 0:
                st.success(
                    f"Simulation complete. "
                    f"Go to the **Results** tab and select `{log_prefix}` from the run list."
                )
            else:
                st.error(f"Simulation exited with code {rc}. Check log above.")


# ===========================================================================
# TAB 2 — Results
# ===========================================================================
with tab_results:
    st.subheader("Simulation Results")

    # --- Run selector ---
    available_runs = []
    if LOGS_DIR.exists():
        available_runs = sorted(
            [d.name for d in LOGS_DIR.iterdir() if d.is_dir()],
            reverse=True,
        )
    # Also include bundled example logs
    example_logs = EXAMPLES_DIR / "logs"
    if example_logs.exists():
        for d in sorted(example_logs.iterdir()):
            if d.is_dir() and (d / "DiseaseReports.tsv").exists():
                available_runs.append(f"examples/logs/{d.name}")

    if not available_runs:
        st.info("No simulation runs found. Run a simulation in the Configure & Run tab first.")
        st.stop()

    # Default to the last run launched from the Configure & Run tab
    last_prefix = st.session_state.get("last_log_prefix")
    default_idx = 0
    if last_prefix and last_prefix in available_runs:
        default_idx = available_runs.index(last_prefix)

    col_sel, col_city, col_reload = st.columns([3, 2, 1])
    with col_sel:
        selected_run = st.selectbox("Select run", available_runs, index=default_idx)
    with col_city:
        map_city = st.selectbox("City (for map)", list(CITY_PROPS.keys()), key="map_city")
    with col_reload:
        st.markdown("&nbsp;", unsafe_allow_html=True)  # vertical alignment spacer
        if st.button("Reload data", use_container_width=True):
            load_disease_reports.clear()

    # Resolve path
    if selected_run.startswith("examples/"):
        reports_path = BASE_DIR / selected_run / "DiseaseReports.tsv"
    else:
        reports_path = LOGS_DIR / selected_run / "DiseaseReports.tsv"

    if not reports_path.exists():
        st.warning(f"DiseaseReports.tsv not found at `{reports_path}`")
        st.stop()

    with st.spinner("Loading simulation data..."):
        df = load_disease_reports(str(reports_path))

    if df.empty:
        st.warning("No data parsed from DiseaseReports.tsv.")
        st.stop()

    max_day = int(df["day"].max()) if not df.empty else 0
    total_agents = df[df["day"] == 0]["agentId"].nunique()

    st.caption(f"Steps: {df['step'].max():,} | Days: {max_day} | Agents (day 0): {total_agents:,}")

    if max_day == 0:
        st.warning(
            "The disease report contains only day 0 (or no data). "
            "The simulation may have exited before completing its first full day. "
            "Check the log output in the Configure & Run tab for errors."
        )
        st.stop()

    # --- Day navigation ---
    if "selected_day" not in st.session_state:
        st.session_state.selected_day = 0
    # Clamp when switching to a shorter run
    st.session_state.selected_day = max(0, min(max_day, st.session_state.selected_day))

    nav_prev, nav_next, nav_slider, nav_goto = st.columns([1, 1, 6, 2])
    with nav_prev:
        if st.button("◀ Prev", use_container_width=True,
                     disabled=(st.session_state.selected_day == 0)):
            st.session_state.selected_day -= 1
            st.rerun()
    with nav_next:
        if st.button("Next ▶", use_container_width=True,
                     disabled=(st.session_state.selected_day == max_day)):
            st.session_state.selected_day += 1
            st.rerun()
    with nav_slider:
        slider_day = st.slider("Day", 0, max_day, st.session_state.selected_day, step=1)
        if slider_day != st.session_state.selected_day:
            st.session_state.selected_day = slider_day
    with nav_goto:
        goto_day = st.number_input(
            "Go to day", min_value=0, max_value=max_day,
            value=st.session_state.selected_day, step=1,
        )
        if int(goto_day) != st.session_state.selected_day:
            st.session_state.selected_day = int(goto_day)
            st.rerun()

    selected_day = st.session_state.selected_day

    day_df = df[df["day"] == selected_day]

    # --- Summary metrics ---
    m1, m2, m3, m4 = st.columns(4)
    for col, status, color in [
        (m1, "Susceptible", "#3498db"),
        (m2, "Exposed", "#f39c12"),
        (m3, "Infectious", "#e74c3c"),
        (m4, "Recovered", "#2ecc71"),
    ]:
        count = int((day_df["diseaseStatus"] == status).sum())
        col.metric(status, f"{count:,}")

    st.divider()

    map_col, chart_col = st.columns([3, 2])

    # --- Maps ---
    with map_col:
        geojson = load_geodata(map_city)
        if geojson is None:
            st.warning(
                f"GeoJSON not found for {map_city}. "
                f"Expected `gui/{map_city.lower().replace(' ', '-')}_regions.geojson`."
            )
        else:
            map_tab_seir, map_tab_report = st.tabs(["SEIR map", "Reporting rate map"])

            with map_tab_seir:
                map_metric = st.selectbox(
                    "Color by",
                    ["Infectious", "Exposed", "Recovered", "Susceptible"],
                    key="map_metric",
                )
                with st.spinner("Rendering map..."):
                    m_seir = build_choropleth(geojson, day_df, map_metric, selected_day)
                st_folium(m_seir, use_container_width=True, height=480, key="seir_map")

            with map_tab_report:
                st.caption(
                    f"Cumulative reporting rate per region — Day 0 to {selected_day}. "
                    "Darker = higher % of infected agents who reported."
                )
                with st.spinner("Rendering map..."):
                    m_report = build_reporting_map(geojson, df, selected_day)
                st_folium(m_report, use_container_width=True, height=480, key="report_map")

    # --- SEIR curves ---
    with chart_col:
        # Build snapshot: for each day, the current count of agents in each state.
        # Each TSV row is a state-change event; forward-fill each agent's last known
        # state across all days to get a true population snapshot.
        df_sorted = df.sort_values(["agentId", "step"])
        last_per_agent_day = (
            df_sorted.groupby(["agentId", "day"])["diseaseStatus"].last().reset_index()
        )
        status_pivot = last_per_agent_day.pivot(
            index="day", columns="agentId", values="diseaseStatus"
        )
        status_pivot = status_pivot.reindex(range(max_day + 1)).ffill()

        # Melt to long form then count — more reliable than apply(value_counts)
        seir_snapshot = (
            status_pivot.reset_index()
            .melt(id_vars="day", var_name="agentId", value_name="diseaseStatus")
            .dropna(subset=["diseaseStatus"])
            .groupby(["day", "diseaseStatus"])
            .size()
            .unstack(fill_value=0)
        )
        for s in ["Susceptible", "Exposed", "Infectious", "Recovered"]:
            if s not in seir_snapshot.columns:
                seir_snapshot[s] = 0

        # Cumulative new cases (E, I, R only — avoids Susceptible dominating the axis)
        first_day_in_state = (
            df_sorted.groupby(["agentId", "diseaseStatus"])["day"].min().reset_index()
        )
        new_per_day = (
            first_day_in_state.groupby(["day", "diseaseStatus"])
            .size()
            .unstack(fill_value=0)
            .reindex(range(max_day + 1), fill_value=0)
        )
        for s in ["Exposed", "Infectious", "Recovered"]:
            if s not in new_per_day.columns:
                new_per_day[s] = 0
        cumulative = new_per_day[["Exposed", "Infectious", "Recovered"]].cumsum()

        # Reporting
        reported_daily = (
            df[df["reported"]]
            .groupby("day").size()
            .reindex(range(max_day + 1), fill_value=0)
            .rename("Reported")
        )
        cumulative_reported = reported_daily.cumsum().rename("Cumulative reported")

        chart_tab1, chart_tab2, chart_tab3 = st.tabs(
            ["SEIR snapshot", "Cumulative", "Reporting"]
        )

        with chart_tab1:
            st.caption("Current agent count per state each day (E/I/R without Susceptible)")
            st.line_chart(
                seir_snapshot[["Exposed", "Infectious", "Recovered"]],
                color=["#f39c12", "#e74c3c", "#2ecc71"],
                height=220,
            )
            with st.expander("Show Susceptible"):
                st.line_chart(
                    seir_snapshot[["Susceptible"]],
                    color=["#3498db"],
                    height=150,
                )

        with chart_tab2:
            st.caption("Cumulative agents who ever entered each state (E/I/R)")
            st.line_chart(
                cumulative,
                color=["#f39c12", "#e74c3c", "#2ecc71"],
                height=220,
            )

        with chart_tab3:
            st.caption("Daily new reported cases and running total")
            st.bar_chart(reported_daily, height=160, color="#e74c3c")
            st.line_chart(cumulative_reported, height=160, color="#3498db")

        st.caption(f"Selected day: {selected_day}")
