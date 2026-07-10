# scAgent-DPM v1.0.0 — First Public Release

**Date:** 2026-07-10

## Highlights

scAgent-DPM is an agentic workflow system for reproducible single-cell drug perturbation analysis. It orchestrates adaptive quality control, per-cell-type differential expression, structured pathway enrichment, and component-aware DPRS scoring into a single auditable pipeline.

### Validated on Real Data

The system was validated on the **scPRAM PBMC drug perturbation benchmark** (GSE279945; 18,868 cells, 7 immune cell types, 146 compounds), producing:
- 48,692 DEG records (2,307 FDR-significant)
- 79,751 pathway tested terms (1,406 FDR-significant)
- 7 DPRS entries with explicit component availability tracking
- 7/7 pipeline modules successful, 0 failures, 0 fallbacks
- 557.6s total runtime
- 29/29 tests passing
- **Reality Score: 85/100**

## Features

- Adaptive quality control with parameter search
- Log-normalized full-gene differential expression
- Per-cell-type DEG with FDR correction
- Structured pathway enrichment (tested vs FDR-significant)
- Component-aware DPRS with NaN for unavailable components
- Module execution tracking with run manifest
- Automated report generation (Markdown, HTML)
- Data validation CLI
- Figure generation (Nature journal style)

## System Requirements

- Python >= 3.10
- scanpy, anndata, numpy, scipy, pandas, matplotlib
- gseapy (for pathway enrichment)
- Optional: celltypist, torch

## Known Limitations

- Per-drug mechanism analysis requires individual drug labels (pooled in current validation)
- scGPT/scGPT-KDMT annotation requires model checkpoints
- Mamba-LSTM dynamics requires model checkpoint and time-course data
- Dose-response analysis requires dose annotations

## Citation

See CITATION.cff or the README for citation information.
