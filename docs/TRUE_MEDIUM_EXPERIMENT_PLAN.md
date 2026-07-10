# True Medium Experiment Plan — scAgent-DPM

**Date:** 2026-06-10
**Status:** DESIGN PHASE — replacing previous "Medium" with properly scoped experiments

---

## Background

The sci-Plex3 MCF7 12-drug experiment (2026-06-05) was a **single-cell-line perturbation pipeline validation**, NOT a complete scAgent-DPM validation. Key gaps: annotation not executed, dynamics not executed, DPRS degenerated (single cell type), pathway enrichment empty, MT gene fallback not active.

This document defines THREE independent medium experiments, each targeting a specific scAgent-DPM module for validation.

---

## Track A: Multi-Cell-Line Drug Response Validation

### Objective
Validate that scAgent-DPM can process multiple cell lines simultaneously, compute per-cell-line per-drug DEG, and compare drug response patterns across cell lines.

### Data
- **Source:** sci-Plex3 (Srivatsan et al. 2020), GSE139944
- **Subset:** MCF7 + A549 + K562, Vehicle + 12 drugs (matching Medium drug list)
- **Cells:** ~100K (3 cell lines × ~33K each, Vehicle + 12 drugs)
- **File:** `sciplex3_multi_cell_line_medium.h5ad`

### What This Validates
- Multi-cell-line data loading and metadata parsing
- Adaptive QC with `group_column=cell_line` (drug-group-aware QC)
- Per-cell-line per-drug DEG
- Cross-cell-line drug response comparison
- DPRS at drug/cell-line level (NOT cell-type level)

### What This Does NOT Validate
- Cell type annotation (cell lines are homogeneous)
- Cell-type-specific DPRS (no immune/stromal subtypes)
- Dynamic state modeling (no time-series)
- Foundation model annotation

### Modules
| Module | Execute? | Rationale |
|--------|----------|-----------|
| data_ingestion | YES | |
| qc | YES | Adaptive, with gene_short_name MT fallback fix |
| preprocessing | YES | |
| annotation | **NO** | Cell lines are pre-labeled; skip |
| perturbation | YES | Per-cell-line per-drug DEG |
| dynamics | **NO** | No time-series data |
| dprs | YES | Drug×cell_line level, 2-3/5 components |
| reporting | YES | |

### Metrics
- Per-cell-line cell retention after QC
- Per-cell-line per-drug DEG count
- Cross-cell-line DEG overlap (Jaccard)
- DPRS ranking by cell line and drug class
- Runtime by cell line

### Outputs
```
results/true_medium/track_a_multi_cell_line/
  data_summary.json
  qc_report.json
  per_cell_line/
    MCF7/deg_results.csv
    A549/deg_results.csv
    K562/deg_results.csv
  cross_cell_line_comparison.csv
  dprs_scores.csv
  report.md
  run_manifest.json
```

### Risk
- **LOW**: Uses same sci-Plex3 data format as verified MCF7 Medium
- **Risk mitigation**: Config already prepared (full_by_cell_line/); start with 3 drugs, then scale to 12

### Publication Role
- **Main text**: Figure showing cross-cell-line drug response
- **Supplementary**: Per-cell-line DEG results

---

## Track B: Cell-Type-Specific Perturbation Validation

### Objective
Validate annotation module and cell-type-specific DPRS on a dataset with genuine cell type heterogeneity (immune, stromal, epithelial subtypes).

### Data Candidates
- **Option B1:** COVID-19 PBMC perturbation (Wilk et al. 2020, or similar): ~10 cell types, drug or disease perturbation
- **Option B2:** Lupus PBMC scRNA-seq with treatment arms: immune cell types + drug treatment
- **Option B3:** Tumor microenvironment dataset with drug treatment: multiple stromal + immune + tumor cell types
- **Option B4:** sci-Plex3 cross-cell-line WITH pooled PBMC or organoid data (if available)

### Selection Criteria (priority order)
1. Has real cell type labels (≥5 distinct cell types)
2. Has drug/perturbation condition (Vehicle + ≥2 treatments)
3. Publicly available as h5ad or easily convertible
4. Cell types have ≥100 cells each in both conditions

### What This Validates
- CellTypist annotation on real heterogeneous data
- Cell-type-specific proportion shift (chi-squared test)
- Cell-type-specific DEG (one DEG set per cell type per drug)
- DPRS with 3-4/5 components: PS + DE + PA + CW
- Annotation confidence weighting in DPRS

### What This Does NOT Validate
- scGPT-KDMT annotation (weights unavailable)
- Foundation model improvement over CellTypist
- Dynamic state modeling
- Mamba-LSTM

### Modules
| Module | Execute? | Rationale |
|--------|----------|-----------|
| data_ingestion | YES | |
| qc | YES | Adaptive QC + MT gene detection fix |
| preprocessing | YES | |
| annotation | **YES (CellTypist)** | scGPT-KDMT optional if weights available |
| perturbation | YES | Per-cell-type per-drug DEG |
| dynamics | **NO** | No time-series |
| dprs | YES | Multi-cell-type, 3-4/5 components |
| reporting | YES | |

### Metrics
- Annotation: cell type count, confidence distribution, low-confidence fraction
- Per-cell-type per-drug DEG counts
- Cell proportion shift significance
- DPRS ranking by cell type × drug
- Pathway enrichment (gene symbol fix applied)

### Outputs
```
results/true_medium/track_b_cell_type_specific/
  data_summary.json
  qc_report.json
  cell_annotation.csv
  annotation_confidence.csv
  per_cell_type/
    {cell_type}/deg_{drug}.csv
  proportion_shift.csv
  pathway_results.csv
  dprs_scores.csv
  report.md
  run_manifest.json
```

### Risk
- **MEDIUM**: Requires finding appropriate dataset; may need data preprocessing
- **Risk mitigation**: Start with dataset search (2 days); fall back to pooled cell lines + artificial labels for pipeline test

### Publication Role
- **Main text**: Figure 3 (annotation) + Figure 4 (cell-type-specific drug response)
- **Core claim**: "Cell-type-specific drug response profiling"

---

## Track C: Dynamic State Transition Validation

### Objective
Validate pseudotime/dynamics module on data with temporal or dose-series structure.

### Data Candidates
- **Option C1:** sci-Plex3 dose-response: MCF7 with multiple doses of a single drug → pseudotime via dose gradient
- **Option C2:** Time-course perturbation: any scRNA-seq dataset with ≥3 time points post-treatment
- **Option C3:** Differentiation time-course with perturbation (e.g., iPSC → neuron + drug)
- **Option C4:** scLifeMamba project data (if accessible from parallel project)

### Selection Criteria
1. Has temporal ordering (≥3 time points or ≥4 dose levels)
2. Has control/reference condition
3. ≥1,000 cells per condition
4. Accessible

### What This Validates
- Pseudotime computation via scanpy DPT
- Control vs treated pseudotime distribution comparison
- EMD/JSD trajectory shift metrics
- Mamba-LSTM interface test (with mock — real model unavailable)

### What This Does NOT Validate
- Mamba-LSTM real inference
- True RNA velocity (spliced/unspliced data required)
- CellRank fate mapping

### Modules
| Module | Execute? | Rationale |
|--------|----------|-----------|
| data_ingestion | YES | |
| qc | YES | |
| preprocessing | YES | |
| annotation | YES (if cell types present) | |
| perturbation | YES | Per-time-point or pooled |
| dynamics | **YES (pseudotime + trajectory shift)** | Core validation target |
| dprs | YES | With trajectory_shift component |
| reporting | YES | |

### Metrics
- Pseudotime correlation with true time/dose ordering (Spearman ρ)
- EMD between control and treated pseudotime distributions
- Per-drug trajectory shift score
- DPRS with TS component active (3-4/5)

### Outputs
```
results/true_medium/track_c_dynamics/
  pseudotime.csv
  trajectory_shift.csv
  control_vs_treated_emd.csv
  dprs_scores.csv
  report.md
  run_manifest.json
```

### Risk
- **HIGH-MEDIUM**: Most challenging to find suitable data; Mamba-LSTM remains mock
- **Risk mitigation**: sci-Plex3 dose-response is the lowest-risk option; pseudotime alone is acceptable

### Publication Role
- **Supplementary Figure**: Pseudotime + trajectory shift
- **Supplementary claim**: "State transition analysis enabled by pseudotime"

---

## Experiment Priority and Timeline

| Priority | Track | Dataset Risk | Module Risk | Time Estimate | Publication Value |
|----------|-------|-------------|-------------|---------------|-------------------|
| **P0** | Track A | LOW | LOW | 2-3 days | HIGH (main Fig 4) |
| **P1** | Track B | MEDIUM | LOW | 1-2 weeks (inc. data search) | HIGHEST (main Figs 3+4) |
| **P2** | Track C | HIGH-MEDIUM | MEDIUM | 2-3 weeks | MEDIUM (supplementary) |

### Execution Order
1. **Track A first** (lowest risk, builds on verified MCF7 Medium, configs already prepared)
2. **Track B second** (highest publication value, enables cell-type-specific claims)
3. **Track C third** (supplementary value, time-permitting)

### Pre-requisites for ALL tracks
- [x] Fix MT gene detection (var.gene_short_name fallback)
- [x] Fix Ensembl ID → gene symbol mapping in DEG output
- [ ] Install WikiPathway (pip install enrichr) on server
- [ ] Test pathway enrichment with gene symbols

---

## What NOT to Do

1. **Do not** claim "6/6 modules complete" — the current Medium ran 4/8 (no annotation, no dynamics)
2. **Do not** claim "cell-type-specific" without Track B data
3. **Do not** claim "dynamic state modeling" without Track C data
4. **Do not** report DPRS with 5/5 components — 3-4/5 is realistic
5. **Do not** launch full-by-cell-line (799K cells) before Tracks A-C complete
6. **Do not** write Results claiming capabilities not yet validated

---

*End of True Medium Experiment Plan*
