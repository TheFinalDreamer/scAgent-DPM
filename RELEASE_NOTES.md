# scAgent-DPM v1.1.0 — CMPB canonical research code release

**Release date:** 2026-10-09
**Predecessor:** v1.0.0 (commit `6f9fb3c`, 2026-07-10)

## What this release is

A curated public snapshot of the **canonical experimental source tree** and archived run records that
produced the results reported in *scAgent-DPM: A Domain-aware and Auditable Workflow for Single-cell
Perturbation Analysis* (CMPB-D-26-07112).

The experimental working tree was never under version control, so this release is a reconstruction
assembled from that tree plus its archived outputs. **`v1.1.0` is a new release identifier and does not
claim to be the historical experimental version number.** File contents of the three core modules are
hash-anchored to an independently sealed manifest produced during the analysis project.

## Why v1.0.0 was superseded

The v1.0.0 snapshot predates two fixes that the manuscript's Methods describe, and a third change to QC
weight handling. In v1.0.0:

1. `src/data/preprocessing.py` applied `normalize_total` + `log1p` **unconditionally**, so the
   processed-log1p scPRAM PBMC input was normalized a second time.
2. `src/agent/executor.py` unconditionally re-normalized the full-gene DEG matrix taken from
   `adata.raw`, applying a second normalization to already-log-normalized input.
3. `src/qc/adaptive_qc.py` had no MT-metric availability handling, so a dataset with no detectable
   mitochondrial genes was still scored against a mitochondrial term that was zero for every cell.

v1.1.0 contains the corrected implementations. The corrected behaviour is what the manuscript
describes and what produced the reported results.

The v1.0.0 documentation also carried a wrong GEO accession (`GSE279945` instead of `GSE96583`),
a "146 compounds" validation scale that does not apply to the primary dataset, stale result counts
(2,307 / 1,406 FDR-significant; 557.6 s runtime), and two CLI commands that were never implemented.
All four categories of error are corrected in this release.

## Validated on real data

Three analysis datasets from two study sources:

| Dataset | Accession | Matrix state | Cells (input -> after QC) | Genes after QC | FDR DEG records | FDR pathway records |
|---|---|---|---|---|---|---|
| scPRAM PBMC (primary) | GSE96583 | processed log1p | 18,868 -> 18,597 | 6,956 | 2,280 | 1,354 |
| sci-Plex4 A549 | GSE139944 | raw UMI counts | 25,301 -> 20,052 | 27,792 | 170 | 4 |
| sci-Plex3 K562 | GSE139944 | raw UMI counts | 7,893 -> 7,777 | 22,532 | 2 | 0 |

All enabled modules completed with no recorded failures. Record counts are records, not unique genes.

## What is in the release

- Canonical source, including the corrected preprocessing, executor and adaptive-QC modules
- Canonical run configurations for all three analyses
- The evaluated test suite (63 tests; the v1.0.0 snapshot shipped 29)
- The fault-injection script and its input validator, so the manuscript's robustness assessment can be
  re-run
- `REPRODUCING.md` (dataset acquisition and run instructions) and `KNOWN_ISSUES.md`

## What is not in the release

- **No expression data.** Obtain the datasets from GEO / scPerturb per `REPRODUCING.md`.
- **No model checkpoints** for scGPT / scGPT-KDMT annotation or Mamba-LSTM dynamics. Those modules are
  disabled in all three canonical runs.
- No intermediate result files from the original analysis project.

## Data licenses

- sci-Plex4 A549 and sci-Plex3 K562 are distributed by scPerturb (Zenodo 10044268) under **CC BY 4.0**.
- The scPRAM PBMC input derives from GSE96583 (Kang et al. 2018) in scGen-preprocessed form, obtained
  through the scPRAM distribution. Consult the original repositories for reuse terms.

## Requirements

Python >= 3.10. The evaluated environment was Python 3.10.6 with scanpy 1.11.5, anndata 0.11.4,
numpy 1.26.4, scipy 1.15.3, pandas 2.3.1 and gseapy 1.3.0.

## Citation

See `CITATION.cff`.

## License

MIT. See `LICENSE`.
