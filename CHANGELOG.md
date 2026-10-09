# Changelog

## v1.1.0 (2026-10-09) — CMPB canonical research code release

Public snapshot assembled from the canonical experimental source tree and archived run records that
produced the results in the CMPB manuscript (CMPB-D-26-07112). The experimental working tree was never
under version control, so this release is a curated reconstruction, not the original experimental
commit. `v1.1.0` is a release identifier only.

### Fixed — analytical behaviour (these are the reason for the release)

- **Matrix-state detection (`src/data/preprocessing.py`).** The previous snapshot applied
  `normalize_total` + `log1p` unconditionally, which double-normalized the processed-log1p scPRAM PBMC
  input. Input matrices are now classified from their value characteristics and a processed-log1p input
  is no longer re-normalized.
- **Conditional DEG matrix preparation (`src/agent/executor.py`).** The previous snapshot
  unconditionally re-normalized the full-gene DEG matrix taken from `adata.raw`, applying a second
  normalization to already-log-normalized input. This now follows the same matrix-state branch as
  preprocessing.
- **MT-metric availability handling (`src/qc/adaptive_qc.py`).** When no mitochondrial genes are
  detected, the mitochondrial-ratio term is now removed from the QC objective and the remaining weights
  are renormalized over the available metrics, instead of scoring against a metric that is zero for
  every cell. For the scPRAM run this yields effective weights `0.25/0.85 = 0.294` and `0.20/0.85 = 0.235`.

### Added

- Canonical run configurations for all three analyses:
  `configs/local/pre_submission_corrected.yaml` (scPRAM PBMC),
  `configs/external_validation/sciplex4_extval_run.yaml` (sci-Plex4 A549),
  `configs/external_validation/sciplex3_extval_run.yaml` (sci-Plex3 K562).
- The evaluated test suite: `tests/test_qc_metric_availability.py`,
  `tests/test_agent_resume_audit.py`, `tests/test_agent_resume_integration.py`
  (the full evaluated set is 63 tests; the previous snapshot shipped 29).
- `tests/robustness_fault_injection.py` and its input validator `validator.py`, so the fault-injection
  assessment reported in the manuscript can be re-run.
- `REPRODUCING.md`, `KNOWN_ISSUES.md`.

### Removed

- `docs/` — the internal development-phase process documents (project overview, proposal report,
  experimental design, dataset selection, system design, reproducibility plan, result-retention
  protocol, manuscript outline, submission-target analysis, next-actions list, experiment plans).
  These were internal planning material, contained superseded framing that the manuscript no longer
  supports, and referenced other unpublished work; they are not needed to reproduce the analyses.
  Reproduction instructions live in `REPRODUCING.md`.

### Changed — documentation only

- `README.md`: rewritten. Accession corrected to **GSE96583** for the primary scPRAM PBMC dataset;
  stale result figures (2,307 / 1,406 FDR-significant, 557.6 s) replaced with the canonical values;
  the "146 compounds" claim removed; scope and statistical boundaries stated explicitly.
- Config paths de-hardcoded: absolute local paths replaced with relative placeholders.
- CLI documentation now lists only the six subcommands that `main.py` actually implements.

### Removed — documentation only

- The `validate-data` and `audit-run` CLI commands advertised by the previous `README.md` /
  `CHANGELOG.md`. These were never implemented; `main.py` exposes `check-env`, `init-project`,
  `run-demo`, `run-pipeline`, `collect-results`, `generate-report`.
- The claim that the config snapshot is "saved correctly in run manifest" (the run manifest's
  `config_snapshot` field is `null`; the snapshot is written as a sibling file).
- The unsubstantiated "Reality Score: 85/100" figure.

### Known limitations

- Dense-matrix input trips a latent guard bug in the DEG path; all canonical datasets are sparse and are
  unaffected. See `KNOWN_ISSUES.md`.
- No automatic-resume command is implemented.
- No content-tamper detection is implemented in the manifest checks.
- scGPT / scGPT-KDMT annotation and Mamba-LSTM dynamics require external checkpoints that are not
  distributed here.

---

## v1.0.0 (2026-07-10) — First public release

Archived for reference. Superseded by v1.1.0.

### Added

- Pipeline executor with modular orchestration (7 core + 2 optional modules)
- Adaptive QC with parameter search over `min_genes` and `max_mt_pct`
- Per-cell-type DEG on a log-normalized full-gene matrix (Wilcoxon + BH correction)
- Pathway v2: structured enrichment with tested/FDR-significant separation, up/down support, local GMT
- DPRS v2: component-aware scoring with `NaN` for unavailable components
- Module status tracking with a run manifest

### Fixed (as described at the time)

- DEG: raw counts preserved in `adata.raw`; DEG uses a log-normalized full-gene matrix
- DPRS: legacy `0.0` placeholder replaced with `NaN` for unavailable components
- Pathway: Ensembl ID filtering, gene-symbol validation, tested/significant separation

### Errata in the v1.0.0 notes

The v1.0.0 `README.md`, `RELEASE_NOTES.md` and this entry contained the following errors, corrected in
v1.1.0:

| Erroneous claim in v1.0.0 | Correction |
|---|---|
| Primary dataset accession `GSE279945` | **GSE96583** (GSE279945 is the unrelated OP3 compound benchmark) |
| "146 compounds" validation scale | The primary dataset has no compound field; it is IFN-beta cytokine stimulation |
| 2,307 FDR-significant DEG records | 2,280 |
| 1,406 FDR-significant pathway terms | 1,354 |
| 557.6 s runtime | 415.2 s |
| `validate-data` and `audit-run` CLI commands | Not implemented |
| "Config snapshot now saved correctly in run manifest" | The run manifest's `config_snapshot` is `null`; the snapshot is a sibling file |
