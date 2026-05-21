#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python}"
DRY_RUN=false
ACTION=""
MODEL_TARGET="all"

usage() {
  cat <<'USAGE'
Usage: ./run.sh [--dry-run] [--model independent|brayton|all] [--data] [--figures] [--smoke-test]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --model) ACTION="model"; MODEL_TARGET="${2:-all}"; shift 2 ;;
    --data) ACTION="data"; shift ;;
    --figures) ACTION="figures"; shift ;;
    --smoke-test) ACTION="smoke-test"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$ACTION" ]]; then
  ACTION="all"
fi

run_model() {
  case "$MODEL_TARGET" in
    independent)
      echo "Running independent reversible benchmark model"
      [[ "$DRY_RUN" == true ]] || "$PYTHON" -c "from models.independent import run_model; run_model()"
      ;;
    brayton)
      echo "Running local-scale Brayton heat-pump architecture-space analyses"
      if [[ "$DRY_RUN" != true ]]; then
        for script in multivariate_analysis.py analyze_efficiency.py generate_regime_validity_sweep.py generate_sensitivity_data.py generate_layer2_layer4_comparison.py; do
          "$PYTHON" "models/thermodynamic/brayton_heat_pump_architecture_space/analysis/$script"
        done
      fi
      ;;
    all)
      MODEL_TARGET=independent run_model
      MODEL_TARGET=brayton run_model
      ;;
    *) echo "Unknown model target: $MODEL_TARGET" >&2; exit 1 ;;
  esac
}

run_data() {
  echo "Refreshing public data mirrors from generated model outputs"
  if [[ "$DRY_RUN" == true ]]; then
    echo "Would copy model output CSVs into data/ subdirectories"
    return 0
  fi
  mkdir -p data/independent data/thermodynamic data/brayton_heat_pump_architecture_space
  cp models/independent/output/*.csv data/independent/
  cp models/thermodynamic/output/*.csv data/thermodynamic/
  cp models/thermodynamic/brayton_heat_pump_architecture_space/output/*.csv data/brayton_heat_pump_architecture_space/
}

run_figures() {
  echo "Regenerating available public figure scripts"
  if [[ "$DRY_RUN" == true ]]; then
    echo "Would run models/figures/fig_*.py"
    return 0
  fi
  for script in models/figures/fig_*.py; do
    "$PYTHON" "$script"
  done
}

run_smoke() {
  echo "Running public smoke tests"
  [[ "$DRY_RUN" == true ]] || "$PYTHON" -m pytest tests/smoke -q
}

case "$ACTION" in
  model) run_model ;;
  data) run_data ;;
  figures) run_figures ;;
  smoke-test) run_smoke ;;
  all) run_model; run_data; run_smoke ;;
  *) echo "Unknown action: $ACTION" >&2; exit 1 ;;
esac
