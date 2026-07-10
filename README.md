# scAgent-DPM

**An agentic workflow for reproducible single-cell drug perturbation analysis.**

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

scAgent-DPM integrates adaptive quality control, perturbation-aware preprocessing, per-cell-type differential expression, structured pathway enrichment with explicit status tracking, and component-aware Drug Perturbation Response Scoring (DPRS).

## Real-Data Validation (scPRAM PBMC, GSE279945)

| Metric | Value |
|--------|-------|
| Cells (pre/post QC) | 18,868 / 18,597 |
| DEG result records | 48,692 (2,307 FDR-significant) |
| Pathway test records | 79,751 (1,406 FDR-significant) |
| DPRS entries | 7 (partial) |
| Pipeline | 7/7 success, 0 failure |
| Runtime | 557.6 s |
| Tests | 29/29 passing |

## Installation

```bash
git clone https://github.com/TheFinalDreamer/scAgent-DPM.git
cd scAgent-DPM
pip install -r requirements.txt
pip install gseapy
```

## Quick Start

```bash
python main.py run-pipeline --config configs/local/local_smoke.yaml
python main.py validate-data --input data.h5ad --config config.yaml --strict
python main.py audit-run --run-dir results/run_dir/
```

## Known Limitations

- Per-drug mechanism: pooled compound treatment; individual labels require sci-Plex3
- scGPT/scGPT-KDMT annotation: requires checkpoints (not included)
- Mamba-LSTM dynamics: requires checkpoint and time-course data

## Citation / License

See [CITATION.cff](CITATION.cff) and [LICENSE](LICENSE).
