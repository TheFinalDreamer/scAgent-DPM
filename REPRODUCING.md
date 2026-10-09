# Reproducing the manuscript analyses

This document describes how to obtain the three analysis inputs and re-run the analyses reported in
the accompanying manuscript *scAgent-DPM: A Domain-aware and Auditable Workflow for Single-cell
Perturbation Analysis* (CMPB-D-26-07112).

**No expression data are redistributed in this repository.** Obtain the datasets from the sources below.

---

## 1. Environment

The evaluated environment was:

| Component | Version |
|---|---|
| Python | 3.10.6 |
| scanpy | 1.11.5 |
| anndata | 0.11.4 |
| numpy | 1.26.4 |
| scipy | 1.15.3 |
| pandas | 2.3.1 |
| gseapy | 1.3.0 |
| platform | Windows 11 Pro (win32) |

```bash
pip install -r requirements.txt
pip install gseapy
```

All three canonical runs used `seed: 42` and `qc.search_iterations: 20`.

---

## 2. Datasets

### 2.1 scPRAM PBMC (primary analysis)

- **Source of record:** the scPRAM paper's PBMC benchmark (Jiang et al. 2024,
  *Bioinformatics* 40(5):btae265). The underlying data are **GSE96583** — Kang et al. 2018, human PBMC
  stimulated with **interferon-beta (IFN-beta)** plus control — used in the scGen-preprocessed form
  distributed with scPRAM.
- **Distribution used:** Zenodo record **10934686** (`scpram-main.zip`).
- **Matrix state:** processed log1p. 7 annotated cell types, 18,868 cells, 6,998 genes.
- **Conditions:** `control` (8,943 cells) vs `stimulated` (9,925 cells).
- **Recorded input hash** (the file actually analysed):

  ```
  file      : scpram_medium.h5ad
  sha256    : 3daa4445a13c8a94f74b8aac9a09da2ebcd33fb4f3da5196e0b4922745d8256d
  ```

  Place it at `data/processed/scpram_medium.h5ad`.

> **Not GSE279945.** Earlier internal records incorrectly cited `GSE279945`, which is the unrelated
> "OP3" compound benchmark (146 compounds, ~301K cells). The primary dataset here is IFN-beta
> stimulation, not a compound panel.

### 2.2 sci-Plex4 A549 (external analysis)

- **Source of record:** Srivatsan et al. 2020, *Science*, **GSE139944**; accessed through the scPerturb
  harmonized collection, Zenodo record **10044268** (`SrivatsanTrapnell2020_sciplex4.h5ad`), **CC BY 4.0**.
- **Matrix state:** raw UMI counts. Subset analysed: A549 cell line, 3 compounds + control.
- **Recorded input hash:**

  ```
  file      : sciplex4_A549_control_3compounds.h5ad
  sha256    : d32fb95e7d17ba5a215f8eb4c6a7122800d5ef13d529d594421f125a5ebc0cee
  ```

  Expected at `03_external_validation/03_processed_data/sciplex4/sciplex4_A549_control_3compounds.h5ad`
  (the path the external-validation config expects, relative to the working directory).

### 2.3 sci-Plex3 K562 (external analysis)

- **Source of record:** same study and collection as above, Zenodo record **10044268**
  (`SrivatsanTrapnell2020_sciplex3.h5ad`), **CC BY 4.0**.
- **Matrix state:** raw UMI counts. Subset analysed: K562 cell line, 5 drugs + control at 10 uM.
- **Recorded input hash:**

  ```
  file      : sciplex3_K562_5drugs_10uM.h5ad
  sha256    : 3886a5a44195cef6fdecd3567a91415ef40246e2bd6b811ccc5e6cbf25a1aee1
  ```

  Expected at `03_external_validation/03_processed_data/sciplex3/sciplex3_K562_5drugs_10uM.h5ad`.

---

## 3. Running each analysis

```bash
# Primary analysis: scPRAM PBMC (processed log1p input)
python main.py run-pipeline --config configs/local/pre_submission_corrected.yaml

# External analysis 1: sci-Plex4 A549 (raw UMI input)
python main.py run-pipeline --config configs/external_validation/sciplex4_extval_run.yaml

# External analysis 2: sci-Plex3 K562 (raw UMI input)
python main.py run-pipeline --config configs/external_validation/sciplex3_extval_run.yaml
```

Config paths are relative placeholders; adjust `input_path` / `output_dir` to your working copy.
The `output_dir` argument is taken from the config by `main.py`.

Pathway enrichment calls Enrichr over the network. To run offline, set
`perturbation.pathway.online: false`; without local GMT gene sets the pathway status will be recorded as
unavailable rather than silently omitted.

---

## 4. Expected outputs

| Dataset | Cells (input -> after QC) | Genes after QC | FDR-passing DEG records | FDR-passing pathway records | Runtime |
|---|---|---|---|---|---|
| scPRAM PBMC | 18,868 -> 18,597 | 6,956 | 2,280 | 1,354 | 415.2 s |
| sci-Plex4 A549 | 25,301 -> 20,052 | 27,792 | 170 | 4 | 282.9 s |
| sci-Plex3 K562 | 7,893 -> 7,777 | 22,532 | 2 | 0 | 202.2 s |

DPRS: scPRAM PBMC 7 entries all `partial`; A549 1 entry `partial`; K562 1 entry
`insufficient_components`.

### Counting conventions

- "FDR-passing DEG records" = rows with `pvals_adj < 0.05` (Benjamini-Hochberg) in
  `merged_deg_results.csv`. **Records, not unique genes:** the 2,280 PBMC records map to 927 distinct
  gene symbols.
- The code also writes a `significant` column that additionally requires `|logFC| > 0.25`. That stricter
  flag gives 2,227 / 95 / 0 for the three datasets and is **not** the convention used above.
- "FDR-passing pathway records" = rows with `Adjusted P-value < 0.05` in `merged_pathway_results.csv`.

### What varies between runs

Analytical outputs (retained cells, retained genes, DEG records, pathway records, DPRS status and score,
output-file count) were identical across three repeated sci-Plex4 executions. **Runtime varied**
(282.9 / 274.3 / 234.2 s) because of I/O and web-service latency. Runtime is not a reproducible quantity
and is not a performance benchmark.

---

## 5. Robustness / fault-injection assessment

```bash
python tests/robustness_fault_injection.py
```

This is a standalone script, not part of the pytest suite. It requires the sci-Plex4 A549 input
(§2.2) and a previously completed sci-Plex4 run directory, and it writes its audit artefacts under
`final_audit/robustness/`. It exercises three scenarios:

| Scenario | Fault injected | Expected | Observed in the reported assessment |
|---|---|---|---|
| R1 | required `obs` field removed in memory | validation failure | `failed_validation` |
| R2 | a manifest-listed output file deleted from a copied run | manifest detects the missing file | `failed_integrity` |
| R3 | `condition_key` set to a non-existent column | validation failure | `failed_validation` |

**Scope limits.** R2 is a **file-existence** check. It does not detect content modification of a file
that is still present. No automatic-resume command exists.

---

## 6. Tests

```bash
python -m pytest tests/ -q          # 63 tests, synthetic data, no downloads
```

---

## 7. Provenance of this release

This repository is a curated public snapshot. The experimental working tree was never under version
control, and the file contents of the core modules are hash-anchored to an independently sealed
manifest produced during the analysis project:

| File | SHA256 |
|---|---|
| `src/data/preprocessing.py` | `62d1c640747c3aa76c21d545202df05ea74cd664e58292a69b7eeb1abf7ac8bc` |
| `src/agent/executor.py` | `e81bd816b866f2fd8498beba264dc57583c0149ecd77eff5e220bd20f42c7fbf` |
| `src/qc/adaptive_qc.py` | `d3a89b75669cc6c9f331aceb1fce6318e930952c0730afd9fd936931ea993187` |
| `src/qc/qc_metrics.py` | `f16e793d10f4c5a3026cc4887ed7644a7afce7607011264b36dbb11ac1c0721a` |
| `src/perturbation/deg.py` | `c52ea393c99abc83f6d0df253a262c3d5950f5c779c0648440f742a5fa93bf99` |
| `src/perturbation/dprs.py` | `183275db56af355b45a5327b206295115fb4039763fbe8a31c81096ac456108c` |
| `src/perturbation/pathway.py` | `0ef6de91d6a5da998f9b44498fa64a7e5028c258c84d290664f967c66a9430f1` |

Verify with:

```bash
sha256sum src/data/preprocessing.py src/agent/executor.py src/qc/adaptive_qc.py \
          src/qc/qc_metrics.py src/perturbation/deg.py src/perturbation/dprs.py \
          src/perturbation/pathway.py
```

`v1.1.0` is a release identifier for this curated snapshot, not the historical experimental version.
