# sci-Plex3 Multi-Cell-Line Medium — Track A Readiness Document

**Date:** 2026-06-10
**Status:** PREPARED — NOT LAUNCHED
**Prerequisite:** Fixed MCF7 medium audit must pass first

---

## 1. Experiment Objective

Validate scAgent-DPM's ability to process multiple cell lines simultaneously: per-cell-line adaptive QC, per-cell-line per-drug DEG, cross-cell-line drug response comparison. This is **cell-line-level**, NOT cell-type-specific analysis.

## 2. Data Construction

### Source
- Raw sci-Plex3: `/data/sc/scAgent_DPM/data/processed/sciplex3/sciplex3_raw.h5ad`
- 799,317 cells, 110,983 genes

### Subset Rules
| Parameter | Value |
|-----------|-------|
| Cell lines | MCF7, A549, K562 |
| Vehicle cap per line | 5,000 cells |
| Drug cap per line per drug | 3,000 cells |
| Random seed | 42 |
| Drugs | 12 (same as MCF7 medium) |

### Selected Drugs (all present in all 3 cell lines)
1. Tacedinaline (CI994) — HDAC inhibitor
2. Baricitinib (LY3009104, INCB028050) — JAK1/2 inhibitor
3. GSK-LSD1 2HCl — LSD1 inhibitor
4. Divalproex Sodium — HDAC inhibitor
5. WP1066 — JAK/STAT inhibitor
6. Tubastatin A HCl — HDAC6 inhibitor
7. Tranylcypromine (2-PCPA) HCl — MAO/LSD1 inhibitor
8. RG108 — DNMT inhibitor
9. CEP-33779 — JAK2 inhibitor
10. Daphnetin — PKC/PKA inhibitor
11. Entacapone — COMT inhibitor
12. PD98059 — MEK inhibitor

### Expected Output Size
~60,000-75,000 cells total (Vehicle: ~15,000 + 12 drugs × ~1,500-2,200 × 3 lines)

### Metadata Columns Preserved
- `perturbation` (created from `product_name`)
- `condition` (Vehicle vs Treated)
- `cell_line` (MCF7 / A549 / K562)
- `cell_group` (= cell_line)
- `gene_short_name` in var
- `dose`, `product_name`, `pathway`, `target`, `pcr_well`

## 3. Pipeline Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| run_annotation | **false** | Cell lines are pre-labeled; no cell type annotation needed |
| run_dynamics | **false** | No time-series or dose-series data |
| per_drug_mode | **true** | Core validation target |
| group_column (QC) | `cell_line` | Per-cell-line QC balance |
| condition_key | `perturbation` | Binary Vehicle vs Drug_i |
| fallback_allowed | **false** | Fail on error for clean validation |
| MT detection | `use_var_symbols: true` | gene_short_name fallback (fixed) |
| DPRS level | cell-line-level | NOT cell-type-specific |

## 4. What This Experiment CAN Claim

| Claim | Status |
|-------|--------|
| Multi-cell-line pipeline execution (3 lines, 12 drugs) | ✓ |
| Per-cell-line adaptive QC with MT gene detection | ✓ |
| Per-cell-line per-drug DEG (cross-cell-line comparison) | ✓ |
| Cell-line-level DPRS (drug × cell_line matrix) | ✓ (2-3/5 components) |
| Gene symbol mapping in DEG output | ✓ |
| Pathway enrichment with gene symbols | ✓ (expected improvement over MCF7-only) |
| Runtime scalability (1 vs 3 cell lines) | ✓ |

## 5. What This Experiment CANNOT Claim

| Claim | Reason |
|-------|--------|
| Cell-type-specific drug response | Only 3 homogeneous cancer cell lines, no immune/stromal subtypes |
| Foundation model annotation | Annotation module not executed |
| Dynamic state transition modeling | Dynamics module not executed |
| Mamba-LSTM validated | Interface-only; not even in this pipeline |
| Trajectory shift revealed | No time/dose ordering |
| scGPT-KDMT annotation performance | Weights unavailable |

## 6. Launch Command

```bash
# Step 1: Create the data subset
cd /data/sc/scAgent_DPM
source /home/audia/miniconda3/etc/profile.d/conda.sh
conda activate scgpt
python scripts/16_create_sciplex3_multicellline_medium.py

# Step 2: Verify the subset
python -c "
import anndata as ad
a = ad.read_h5ad('data/processed/sciplex3/sciplex3_medium_multicellline.h5ad')
print(f'{a.n_obs} cells, {a.n_vars} genes')
print(f'cell_lines: {sorted(a.obs.cell_line.unique())}')
print(f'drugs: {a.obs.perturbation.nunique()} unique')
print(f'has gene_short_name: {\"gene_short_name\" in a.var.columns}')
"

# Step 3: Launch experiment (ONLY after fixed MCF7 medium audit passes)
tmux new -d -s sciplex3_multicellline_medium "
cd /data/sc/scAgent_DPM &&
source /home/audia/miniconda3/etc/profile.d/conda.sh &&
conda activate scgpt &&
python main.py run-pipeline --config configs/real_sciPlex3_medium_multicellline.yaml \
2>&1 | tee logs/server_runs/sciplex3_multicellline_medium_\$(date +%Y%m%d_%H%M%S).log
"
```

## 7. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Data creation script errors (NaN in product_name, column mismatch) | LOW | Tested product_name matching logic; raw data confirmed 189 string products |
| Cell line imbalance (MCF7 has more cells than A549/K562) | LOW | Caps applied (3,000/5,000 per group); all lines ≥900 cells/drug |
| Pathway enrichment still empty with gene symbols | MEDIUM | May need larger DEG sets; KEGG_2021 may not recognize all symbols |
| DPRS degenerated (all cell lines similar response) | LOW | DPRS at cell-line level with 3 groups gives meaningful comparison |
| Runtime too long (~3× MCF7 = ~3 hours) | LOW | Acceptable for medium experiment; server has 128 cores |

## 8. Dependencies

- [x] MT gene detection fix verified (smoke test: 37 genes, 18.58% pct_mt)
- [x] DEG gene_symbol mapping code patched
- [ ] Fixed MCF7 medium audit complete (currently running on server)
- [ ] Fixed MCF7 medium: gene_symbol column confirmed in DEG output
- [ ] Fixed MCF7 medium: pathway enrichment status confirmed
- [ ] Data creation script executed successfully

## 9. DO NOT START Until

1. Fixed MCF7 medium experiment completes successfully
2. Fixed MCF7 medium audit confirms:
   - mt_genes_detected > 0
   - mt_gene_source = var:gene_short_name
   - DEG output includes gene_symbol column
   - All outputs written correctly

---

*Track A prepared 2026-06-10. Awaiting fixed MCF7 medium completion.*
