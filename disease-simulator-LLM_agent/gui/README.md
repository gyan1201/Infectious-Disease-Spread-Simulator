# Disease Simulator GUI

Streamlit front-end for `vanilla-0.1-jar-with-dependencies.jar`.

## Python version requirement

Streamlit 1.12.1+ explicitly excludes **Python 3.9.7** due to a known asyncio bug in that patch release. Use Python 3.9.8+, 3.10, or 3.11.

If your default Python is 3.9.7 (e.g. Anaconda base), create a new environment first:

```bash
conda create -n sim-gui python=3.10 -y
conda activate sim-gui
```

## Setup

```bash
cd gui
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens at http://localhost:8501

## Tabs

### Configure & Run
- Pick city, reporting model (LLM / LR), scenario (S1/S2/S3)
- Set key SEIR parameters (agents, seed, probabilities, duration)
- Click **Run Simulation** — streams Java log output live
- Output written to `logs/<prefix>/`

### Results
- Select any completed run from `logs/` (or bundled `examples/logs/`)
- **Day slider** — scrub through each simulation day
- **Choropleth map** — region-level counts colored by Infectious / Exposed / Recovered / Susceptible
- **SEIR curves** — line chart across all days
- **Reported cases** — bar chart of daily reported cases

## Prerequisites

The JAR must be built first:

```bash
cd ..
mvn org.apache.maven.plugins:maven-resources-plugin:2.6:resources \
  org.apache.maven.plugins:maven-compiler-plugin:3.1:compile \
  org.apache.maven.plugins:maven-assembly-plugin:3.1.0:single
```
