# Changelog

## v1.0.0 (2026-07-10) — First Public Release

### Added
- Pipeline executor with modular orchestration (7 core + 2 optional modules)
- Adaptive QC with parameter search over min_genes and max_mt_pct
- Per-cell-type DEG on log-normalized full-gene matrix (Wilcoxon + BH correction)
- Pathway v2: structured enrichment with tested/FDR-significant separation, up/down support, local GMT
- DPRS v2: component-aware scoring with NaN-based missing-component handling
- Data validator with CLI (validate-data command)
- Agent execution with module status tracking, manifest, and audit commands
- Real data validation on scPRAM PBMC (GSE279945): 18,868 cells, 48,692 DEGs, 79,751 pathways
- 29 unit and integration tests (all passing)
- Reality audit framework (85/100)
- Figure generation from real data (9 figures, Nature journal style)

### Fixed
- DEG: raw counts now preserved in adata.raw; DEG uses log-normalized full-gene matrix
- DPRS: legacy 0.0 placeholder replaced with NaN for unavailable components
- Pathway: Ensembl ID filtering, gene symbol validation, tested/significant separation
- Executor: per-drug x cell_type DEG decomposition
- Config snapshot now saved correctly in run manifest
- Fallback mechanism now properly propagates status

### Known Limitations
- scGPT/scGPT-KDMT annotation requires model checkpoints (not included)
- Mamba-LSTM dynamics requires model checkpoint and time-course data
- Per-drug mechanism analysis requires individual drug labels (pooled in current validation)
