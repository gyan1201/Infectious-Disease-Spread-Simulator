#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh  —  Git Bash / Linux / macOS launcher for the disease simulator
# Can be called from any directory:  bash run.sh [log-prefix] [days]
# Output always goes to disease-simulator-main/logs/<prefix>/
# ---------------------------------------------------------------------------

# Resolve the directory containing this script so paths are always correct
# regardless of where the user calls run.sh from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PREFIX="${1:-atl-test}"
DAYS="${2:-90}"
UNTIL=$(( DAYS * 288 ))   # 5 min/step × 288 steps = 1 day

echo "Running simulation: prefix=$PREFIX  days=$DAYS  steps=$UNTIL"
echo "Output: $SCRIPT_DIR/logs/$PREFIX/"

java \
  "-Dlog4j2.configurationFactory=edu.gmu.mason.vanilla.log.CustomConfigurationFactory" \
  "-Dlog.rootDirectory=$SCRIPT_DIR/logs" \
  "-Dfile.prefix=$PREFIX" \
  "-Dsimulation.test=bias" \
  -jar "$SCRIPT_DIR/target/vanilla-0.1-jar-with-dependencies.jar" \
  -configuration "$SCRIPT_DIR/examples/atlanta.properties" \
  -bias.config "$SCRIPT_DIR/examples/bias.llm.properties" \
  -bias.single.config "$SCRIPT_DIR/examples/bias.single.properties" \
  -decision.bank "$SCRIPT_DIR/examples/llm.atl.csv" \
  -until "$UNTIL"

RC=$?
if [ $RC -ne 0 ]; then
  echo ""
  echo "Simulation failed with exit code $RC"
  exit $RC
fi

echo ""
echo "Done. Results in $SCRIPT_DIR/logs/$PREFIX/"
