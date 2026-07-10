#!/bin/bash
# scAgent-DPM: Server batch experiment runner
# Run with: bash scripts/server_run_all.sh

set -e

SERVER_PATH="${SERVER_PATH:-/data/sc/scAgent_DPM}"
CONDA_ENV="scagent-dpm"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="${SERVER_PATH}/logs/server_runs"
RESULT_DIR="${SERVER_PATH}/results/server_runs"

echo "============================================"
echo "  scAgent-DPM Server Batch Runner"
echo "  Started: $(date)"
echo "  Server Path: ${SERVER_PATH}"
echo "============================================"

# Create directories
mkdir -p "${LOG_DIR}"
mkdir -p "${RESULT_DIR}"

# Activate conda
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV}"

cd "${SERVER_PATH}"

# --- Step 1: Environment Check ---
echo ""
echo "[1/8] Checking environment..."
python main.py check-env 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_01_env_check.log"

# --- Step 2: Demo Pipeline ---
echo ""
echo "[2/8] Running demo pipeline..."
python main.py run-demo --config configs/demo.yaml 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_02_demo.log"

# --- Step 3: QC Experiments ---
echo ""
echo "[3/8] Running QC experiments..."
python main.py run-pipeline --config configs/experiment_qc.yaml 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_03_qc.log"

# --- Step 4: Annotation Experiments ---
echo ""
echo "[4/8] Running annotation experiments..."
python main.py run-pipeline --config configs/experiment_annotation.yaml 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_04_annotation.log"

# --- Step 5: Perturbation Experiments ---
echo ""
echo "[5/8] Running perturbation experiments..."
python main.py run-pipeline --config configs/experiment_perturbation.yaml 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_05_perturbation.log"

# --- Step 6: Dynamics Experiments ---
echo ""
echo "[6/8] Running dynamics experiments..."
python main.py run-pipeline --config configs/experiment_dynamics.yaml 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_06_dynamics.log"

# --- Step 7: Collect Results ---
echo ""
echo "[7/8] Collecting results..."
python main.py collect-results --input "${RESULT_DIR}" --output "${RESULT_DIR}/summary" 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_07_collect.log"

# --- Step 8: Generate Final Report ---
echo ""
echo "[8/8] Generating final report..."
# Find the latest run directory
LATEST_RUN=$(ls -dt "${RESULT_DIR}"/*/ 2>/dev/null | head -1)
if [ -n "${LATEST_RUN}" ]; then
    python main.py generate-report --run-dir "${LATEST_RUN}" 2>&1 | tee "${LOG_DIR}/${TIMESTAMP}_08_report.log"
fi

# --- Final Summary ---
echo ""
echo "============================================"
echo "  Server Batch Complete"
echo "  Finished: $(date)"
echo "  Logs: ${LOG_DIR}/${TIMESTAMP}_*.log"
echo "  Results: ${RESULT_DIR}"
echo "============================================"

# Generate server run summary
cat > "${RESULT_DIR}/FINAL_SERVER_RUN_SUMMARY.md" << EOF
# scAgent-DPM Server Run Summary

- **Date:** $(date)
- **Server Path:** ${SERVER_PATH}
- **Conda Env:** ${CONDA_ENV}

## GPU Info
\`\`\`
$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null || echo "nvidia-smi not available")
\`\`\`

## Disk Space
\`\`\`
$(df -h ${SERVER_PATH} 2>/dev/null || echo "df not available")
\`\`\`

## Experiment Logs
| Step | Log File |
|------|----------|
| 1. Env Check | ${LOG_DIR}/${TIMESTAMP}_01_env_check.log |
| 2. Demo | ${LOG_DIR}/${TIMESTAMP}_02_demo.log |
| 3. QC | ${LOG_DIR}/${TIMESTAMP}_03_qc.log |
| 4. Annotation | ${LOG_DIR}/${TIMESTAMP}_04_annotation.log |
| 5. Perturbation | ${LOG_DIR}/${TIMESTAMP}_05_perturbation.log |
| 6. Dynamics | ${LOG_DIR}/${TIMESTAMP}_06_dynamics.log |
| 7. Collect | ${LOG_DIR}/${TIMESTAMP}_07_collect.log |
| 8. Report | ${LOG_DIR}/${TIMESTAMP}_08_report.log |

## Notes
- Review each log file for detailed status
- Check for FALLBACK markers in results
- Real model results require valid model weights in config
EOF

echo "Summary generated: ${RESULT_DIR}/FINAL_SERVER_RUN_SUMMARY.md"
