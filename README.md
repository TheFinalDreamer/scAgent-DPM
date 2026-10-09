# scAgent-DPM

**A domain-aware, state-aware workflow for reproducible single-cell perturbation analysis.**

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

scAgent-DPM orchestrates input validation, schema harmonization, matrix-state-aware preprocessing,
metric-aware adaptive quality control, per-cell-type differential expression, structured pathway
enrichment and component-aware Drug Perturbation Response Scoring (DPRS) into a single auditable
workflow with explicit state tracking.

## Scope and framing

- **scAgent-DPM is a rule-based, domain-aware workflow.** "Agentic" here means rule-based,
  configuration-driven orchestration of a predefined module graph. It is **not** an LLM-based
  autonomous agent, and it contains no language model, foundation model or autonomous reasoning.
- It is a **workflow / orchestration layer**, not a predictive perturbation-response model and not a
  causal-inference method. It does not predict unseen drug responses, rank drugs by efficacy, model
  dose-response, or replace the underlying statistical methods (Scanpy, gseapy, ...).
- Its contribution is making perturbation-specific assumptions explicit: which matrix state an input is
  in, which components are available for a given dataset, and what provenance each run emitted.

## Version and provenance of this release

**Release:** `v1.1.0` - *CMPB canonical research code release*

This release is a **curated public snapshot assembled from the canonical experimental source tree and
archived run records** that produced the results reported in *scAgent-DPM: A Domain-aware and Auditable
Workflow for Single-cell Perturbation Analysis* (CMPB-D-26-07112).
It is **not** a Git commit created on the date of the original experiments; the experimental working
tree was never under version control. The version number `v1.1.0` is a new release identifier only and
does not claim to be the historical experimental version number.

The predecessor `v1.0.0` snapshot (commit `6f9fb3c`) predates two fixes that the manuscript's Methods
describe. See [`CHANGELOG.md`](CHANGELOG.md) and [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).

## Analyses and data sources

Three analysis datasets drawn from **two study sources**:

| Dataset | Source study | GEO accession | Matrix state | Cells (input -> after QC) | Genes after QC |
|---|---|---|---|---|---|
| scPRAM PBMC (primary) | scPRAM PBMC benchmark (Jiang et al. 2024); original data Kang et al. 2018, IFN-beta stimulation, scGen-preprocessed | **GSE96583** | processed log1p | 18,868 -> 18,597 | 6,956 |
| sci-Plex4 A549 | Srivatsan et al. 2020, via the scPerturb harmonized collection (Zenodo 10044268, CC BY 4.0) | **GSE139944** | raw UMI counts | 25,301 -> 20,052 | 27,792 |
| sci-Plex3 K562 | Srivatsan et al. 2020, via the scPerturb harmonized collection (Zenodo 10044268, CC BY 4.0) | **GSE139944** | raw UMI counts | 7,893 -> 7,777 | 22,532 |

> **Note on the primary dataset.** The scPRAM PBMC benchmark is derived from **GSE96583**
> (Kang et al. 2018) and its perturbation is **IFN-beta cytokine stimulation**, not a drug panel.
> Only the two sci-Plex datasets are compound perturbations. Earlier snapshots of this repository cited
> `GSE279945`; that is a different dataset (the "OP3" compound benchmark) and was a conflation. It has
> been corrected here.

## Canonical results reported in the manuscript

| Dataset | FDR-passing DEG records | FDR-passing pathway records | Runtime |
|---|---|---|---|
| scPRAM PBMC | 2,280 | 1,354 | 415.2 s |
| sci-Plex4 A549 | 170 | 4 | 282.9 s |
| sci-Plex3 K562 | 2 | 0 | 202.2 s |

Counts are **records, not unique genes** (the 2,280 PBMC records correspond to 927 distinct gene
symbols). FDR-passing is `pvals_adj < 0.05` (Benjamini-Hochberg). The code additionally exposes a
`significant` column applying a `|logFC| > 0.25` filter on top of the FDR threshold; that stricter
in-code flag yields different counts and is **not** the convention used for the numbers above. Runtime
varies between executions (see *Reproducibility scope* below).

## Methods as implemented

### Matrix-state-aware preprocessing

Input matrices are classified before preprocessing from their value characteristics
(`src/data/preprocessing.py`):

- **Processed log1p input** (max expression < 20, non-integer) is **not re-normalized** - the pipeline
  detects this state and skips `normalize_total` + `log1p`.
- **Raw UMI-count input** is normalized by total-count scaling to 10,000 followed by `log1p`.

The scPRAM PBMC input is processed log1p; both sci-Plex inputs are raw UMI counts. The DEG matrix
follows the same conditional path (`src/agent/executor.py`), so a log1p input is not double-normalized.

### Metric-aware adaptive QC

`src/qc/adaptive_qc.py` runs a seeded (`seed = 42`) random search over a two-parameter space: per-cell
`min_genes` and maximum mitochondrial fraction `max_mt_pct`. The `min_genes` bounds come from the 1st
and 50th percentiles of per-cell detected-gene counts (floor 50); the `max_mt_pct` bounds span 5% to
the 99th percentile + 5 percentage points (capped at 50%). Twenty parameter samples are scored by a
weighted composite objective rewarding retained-cell ratio, retained-gene ratio and mitochondrial-ratio
control. Gene filtering uses a fixed `min_cells = 3`.

Mitochondrial genes are detected from gene-name evidence: an organism-specific prefix (`MT-` / `mt-`)
matched against variable names, with a fallback search over gene-symbol columns in `adata.var`
(`gene_short_name`, `gene_symbol`, `symbol`, `gene_name`, `hgnc_symbol`). **When no MT genes are found,
the mitochondrial-ratio metric is recorded as unavailable rather than imputed: the mitochondrial term is
removed from the objective and the remaining weights are renormalized over the available metrics.**
Because the mitochondrial fraction is then zero for every cell, the `max_mt_pct` filter has no effect.
For the scPRAM run this renormalization is `0.25/0.85 = 0.294` (cell retention) and `0.20/0.85 = 0.235`
(gene retention). Per-dataset QC configuration is in `configs/`.

### Differential expression

`src/perturbation/deg.py` computes DEGs with `sc.tl.rank_genes_groups` using the **Wilcoxon rank-sum
test** with **Benjamini-Hochberg** FDR correction, grouped **per cell type**, comparing treated against
control.

**Statistical boundary.** In the two sci-Plex datasets all treated cells are pooled into a single
`treated` arm and compared against pooled control within each cell line - no per-compound decomposition
is performed. The scPRAM PBMC run compares `stimulated` against `control` pooled across cells within
each of the seven annotated cell types. These are **pooled** contrasts; they do not support
compound-specific mechanism inference, dose-response modelling, or comparative pharmacological ordering.

### Pathway enrichment

`src/perturbation/pathway.py` runs gseapy Enrichr against KEGG 2021 Human, WikiPathway 2021 Human and
GO Biological Process 2021, for up- and down-regulated gene sets separately, with explicit status
tracking (`available` / `empty` / `insufficient_genes` / `unavailable` / `error`) so that "tested but
not significant" is distinguishable from "not tested".

### DPRS

`src/perturbation/dprs.py` computes a **component-aware descriptive summary**, not a predictive model.
Five components are defined - proportion shift (PS), DEG intensity (DE), pathway activity (PA),
trajectory shift (TS) and confidence weight (CW) - with default weights 0.30 / 0.25 / 0.20 / 0.15 /
0.10. Components that are unavailable for a dataset are **excluded** and the remaining weights are
renormalized; unavailable components are reported as `unavailable`, never imputed. Each row carries a
status:

- `valid` - at least 4 components available
- `partial` - 2-3 components available
- `insufficient_components` - fewer than 2 available (`normalized_score` is `NaN`)
- `failed` - computation error

In the reported runs: scPRAM PBMC -> 7 entries, all `partial` (PS, DE, PA available); sci-Plex4 A549 ->
1 entry, `partial`; sci-Plex3 K562 -> 1 entry, `insufficient_components` (only DE available).

### Provenance and state tracking

Each run emits a **run manifest** (per-module status and duration), a **config snapshot**, an
**environment snapshot**, an **execution graph**, a **reproducibility metadata file** and an **output
manifest**. Module statuses (`success` / `failure` / `fallback` / `skipped`) and component availability
values form a controlled status ontology.

Two distinct things are often both called "checksums" - they are **not** the same here:

| | What it is | Where |
|---|---|---|
| **A. Pipeline output manifest** | a listing of emitted files with **path and size only** - no content hash | `output_manifest.csv`, written by `src/agent/executor.py` |
| **B. Audit / source-data layer** | an independent **SHA256 manifest of file contents**, generated by post-run audit tooling and re-verifiable | produced by the analysis project's audit scripts, **not** by the workflow runtime |

A SHA256 helper (`compute_file_checksum`) exists in `src/utils/reproducibility.py` but is **not wired
into the workflow's own output manifest**. The pipeline output manifest should not be described as
"checksum-backed".

### Robustness and fault handling

A fault-injection assessment (script: `tests/robustness_fault_injection.py`) exercised three predefined
scenarios on the sci-Plex4 A549 input and a copied clean-run directory:

| Scenario | Injected fault | Observed |
|---|---|---|
| R1 missing metadata | removed `obs['condition']` from an in-memory copy | validation failure with explicit message |
| R2 deleted output | deleted a manifest-listed intermediate file from a copied run | manifest check reports the missing file |
| R3 schema mismatch | set `condition_key` to a non-existent column | validation failure with explicit message |

R2 detects a **deleted** file by existence checking. It does **not** demonstrate detection of content
tampering (a modified but present file). No automatic-resume command is implemented; the workflow
provides state persistence and audit-supported recovery, not fault-tolerant resumption.

### Reproducibility scope

Repeated sci-Plex4 executions in a **fixed environment** produced identical analytical outputs (retained
cells/genes, DEG records, pathway records, DPRS status and score, output-file count) while wall-clock
runtime varied (282.9 / 274.3 / 234.2 s) with I/O and backend latency.

**Same-environment repeat consistency is not cross-environment reproducibility.** No claim is made that
these results reproduce under a different operating system, package version set, CPU architecture, or
random-number library. All results come from one environment (Python 3.10.6, scanpy 1.11.5,
anndata 0.11.4).

## Installation

```bash
git clone https://github.com/TheFinalDreamer/scAgent-DPM.git
cd scAgent-DPM
pip install -r requirements.txt
pip install gseapy
```

Pathway enrichment uses Enrichr over the network by default. For offline use, pass
`perturbation.pathway.online: false` together with local GMT paths; without local gene sets the pathway
status is recorded as unavailable rather than silently dropped.

## Quick start

The CLI exposes six subcommands:

```bash
python main.py check-env
python main.py init-project
python main.py run-demo     --config configs/demo.yaml
python main.py run-pipeline --config configs/local/pre_submission_corrected.yaml
python main.py collect-results --input results/ --output reports/
python main.py generate-report --run-dir results/<run_dir>/
```

Verify the CLI surface at any time with `python main.py --help`. Only the subcommands listed there exist.

## Reproducing the manuscript analyses

See [`REPRODUCING.md`](REPRODUCING.md) for dataset acquisition steps, recorded input hashes, the exact
configuration files for all three analyses and the expected output counts.

## Testing

```bash
python -m pytest tests/ -q
```

The suite covers configuration handling, data loading, QC metric availability (including the MT
fallback and weight renormalization), DPRS computation and status classification, reporting, and agent
state persistence behaviour. Tests use synthetic data and require no downloads.

The fault-injection script is a standalone program (not part of the pytest suite) and requires the
sci-Plex4 external-validation input to be present; see `REPRODUCING.md`.

## Known limitations

- **Per-compound mechanism analysis is not supported.** Both sci-Plex datasets are analysed as pooled
  treated-vs-control contrasts.
- **scGPT / scGPT-KDMT annotation** requires model checkpoints that are not distributed here.
- **Mamba-LSTM dynamics** requires a model checkpoint and time-course data; not distributed here.
- **Dense-matrix input** triggers a latent guard bug in the DEG path. All canonical datasets are sparse
  and are unaffected. See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
- **No automatic resume** command is implemented.
- **No content-tamper detection** is implemented in the manifest checks.

## Citation and license

See [`CITATION.cff`](CITATION.cff) and [`LICENSE`](LICENSE) (MIT).

## Data availability

The scPRAM PBMC input derives from **GSE96583** (Kang et al. 2018), obtained through the scPRAM
distribution in scGen-preprocessed form. The sci-Plex4 A549 and sci-Plex3 K562 inputs derive from
**GSE139944** (Srivatsan et al. 2020) and were accessed through the scPerturb harmonized collection
(Zenodo record 10044268, CC BY 4.0). No expression data are redistributed in this repository; consult
the original repositories for dataset-specific reuse terms.
