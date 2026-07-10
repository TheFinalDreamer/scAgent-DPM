# scAgent-DPM Next Actions (Updated 2026-06-10)

## Status Summary

**Completed:** Demo, Pilot (4-drug), MCF7 pipeline validation (12-drug), literature (49 papers), manuscript drafts (v0.1), code audit, bug fixes (P0×2, MT gene, Ensembl mapping)

**Current bottleneck:** No multi-cell-type data → DPRS degenerated. No time-series data → dynamics not tested. scGPT-KDMT and Mamba-LSTM remain interface-only (weights unavailable).

---

## P0: Must Fix Before Any Paper Claim

- [ ] **Re-run MCF7 pipeline with fixed MT gene detection** (code fixed 2026-06-10, smoke test passed)
- [ ] **Re-run MCF7 pipeline with gene symbol mapping** (deg.py fixed, needs DEG re-computation)
- [ ] **Re-run pathway enrichment with gene symbols** (after DEG re-run)
- [ ] **Implement doublet detection** (scrublet code — currently zero implementation)
- [ ] **Install WikiPathway (pip install enrichr) on server**

## P1: True Medium Experiments (see `docs/TRUE_MEDIUM_EXPERIMENT_PLAN.md`)

### Track A: Multi-Cell-Line Drug Response (LOW risk, 2-3 days)
- [ ] Create multi-cell-line h5ad subset (MCF7 + A549 + K562, 12 drugs)
- [ ] Run pipeline with `group_column=cell_line`
- [ ] Validate cross-cell-line DEG comparison
- [ ] Config already prepared: `configs/full_by_cell_line/`

### Track B: Cell-Type-Specific Perturbation (HIGHEST pub value, 1-2 weeks)
- [ ] Search for PBMC or heterogeneous perturbation dataset (≥5 cell types, ≥2 conditions)
- [ ] Run full pipeline with annotation (CellTypist), per-cell-type DEG, DPRS
- [ ] This enables the "cell-type-specific drug response" core claim

### Track C: Dynamic State Validation (MEDIUM risk, 2-3 weeks)
- [ ] Find time-course or dose-series perturbation data
- [ ] Run pipeline with dynamics module (pseudotime + trajectory shift)
- [ ] Mamba-LSTM remains interface-only for now

## P2: Module Completion

- [ ] Create target_prioritization module (src code — currently nonexistent)
- [ ] Integrate visualization code into pipeline (plot_*.py defined but never called)
- [ ] Integrate validators into executor (defined but never called)
- [ ] Add intermediate AnnData checkpoint saves

## P3: Foundation Model Integration (Dependent on external projects)

- [ ] Obtain scGPT-KDMT weights from 2nd paper project
- [ ] Implement real scGPT-KDMT inference (replace mock)
- [ ] Implement real Mamba-LSTM inference or confirm infeasible for available data
- [ ] Benchmark: CellTypist vs scGPT-KDMT annotation accuracy

## Writing Tasks

- [x] Literature survey, BibTeX, summaries
- [x] Innovation point refinement
- [x] Paper outline and method framework
- [x] Introduction/Results/Discussion drafts (v0.1)
- [x] Cleaned Results draft (v0.2, claims-audited)
- [ ] Revise Introduction draft per claims audit
- [ ] Revise Discussion draft per claims audit (add limitation section)
- [ ] Generate Figures 1-7 (pending data from Track A/B/C)
- [ ] Generate Tables 1-6

## DO NOT START Yet

- Full-by-cell-line experiment (799K cells) — wait for Tracks A-C to complete
- scGPT-KDMT annotation benchmarking — wait for weights
- Mamba-LSTM full validation — wait for time-series data
- Ablation study — requires complete multi-module pipeline to ablate
- Journal submission — target Aug-Sep 2026
