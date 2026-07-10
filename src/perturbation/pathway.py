"""Pathway enrichment analysis with structured status tracking.

Supports: gseapy (online Enrichr), local GMT files.
Tracks per-enrichment status with failure reasons.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger("scagent_dpm.perturbation.pathway")

# Enrichr database aliases for gseapy
ENRICHR_DB_MAP = {
    "KEGG_2021_Human": "KEGG_2021_Human",
    "KEGG_2019_Human": "KEGG_2019_Human",
    "Reactome_2022": "Reactome_2022",
    "WikiPathway_2021_Human": "WikiPathway_2021_Human",
    "GO_Biological_Process_2021": "GO_Biological_Process_2021",
    "GO_Biological_Process_2023": "GO_Biological_Process_2023",
}


def run_pathway_enrichment(
    deg_df: pd.DataFrame,
    gene_col: str = "gene_symbol",
    fallback_gene_col: str = "names",
    cell_type_col: str = "cell_type",
    drug_col: str = "drug",
    databases: Optional[List[str]] = None,
    organism: str = "human",
    direction_col: Optional[str] = None,
    min_genes: int = 5,
    local_gmt_paths: Optional[Dict[str, str]] = None,
    online: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run pathway enrichment for DEGs with structured status tracking.

    Returns
    -------
    pathway_df : DataFrame with enrichment results
    status_df : DataFrame with per-enrichment-attempt status
    """
    if databases is None:
        databases = ["KEGG_2021_Human"]

    status_records = []
    all_results = []

    # Determine grouping columns
    group_cols = [cell_type_col]
    if drug_col in deg_df.columns:
        group_cols.append(drug_col)

    # Resolve gene column: prefer gene_symbol, fall back to names
    effective_gene_col = gene_col if gene_col in deg_df.columns else fallback_gene_col
    gene_source = effective_gene_col

    for group_keys, group_df in deg_df.groupby(group_cols):
        # Build group label
        if isinstance(group_keys, tuple):
            group_label = "|".join(str(k) for k in group_keys)
            ct = str(group_keys[0])
            drug = str(group_keys[1]) if len(group_keys) > 1 else None
        else:
            group_label = str(group_keys)
            ct = str(group_keys)
            drug = None

        # Extract and clean gene symbols
        raw_genes = group_df[effective_gene_col].dropna().unique().tolist()
        cleaned_genes = _clean_gene_list(raw_genes)

        status_base = {
            "group": group_label,
            "cell_type": ct,
            "drug": drug if drug else ct,
            "input_gene_count": len(raw_genes),
            "recognized_gene_count": len(cleaned_genes),
            "gene_source": gene_source,
        }

        if len(cleaned_genes) < min_genes:
            status_records.append({
                **status_base,
                "pathway_status": "insufficient_genes",
                "database": "all",
                "direction": "both",
                "significant_pathway_count": 0,
                "failure_reason": f"Only {len(cleaned_genes)} valid genes; min {min_genes} required",
            })
            continue

        # Try up/down separation if logfoldchanges available
        directions = ["both"]
        if direction_col and direction_col in group_df.columns:
            directions = ["up", "down"]

        for direction in directions:
            dir_genes = cleaned_genes
            if direction == "up":
                up_mask = group_df[effective_gene_col].isin(cleaned_genes) & (group_df.get("logfoldchanges", 0) > 0)
                dir_genes = group_df[up_mask][effective_gene_col].dropna().unique().tolist()
                dir_genes = _clean_gene_list(dir_genes)
            elif direction == "down":
                down_mask = group_df[effective_gene_col].isin(cleaned_genes) & (group_df.get("logfoldchanges", 0) < 0)
                dir_genes = group_df[down_mask][effective_gene_col].dropna().unique().tolist()
                dir_genes = _clean_gene_list(dir_genes)

            if len(dir_genes) < min_genes:
                status_records.append({
                    **status_base,
                    "pathway_status": "insufficient_genes",
                    "database": "all",
                    "direction": direction,
                    "significant_pathway_count": 0,
                    "failure_reason": f"Only {len(dir_genes)} genes for {direction}; min {min_genes} required",
                })
                continue

            for db in databases:
                status = dict(status_base)
                status["database"] = db
                status["direction"] = direction

                # Try local GMT first
                gmt_path = None
                if local_gmt_paths and db in local_gmt_paths:
                    gmt_path = local_gmt_paths[db]

                try:
                    if gmt_path and Path(gmt_path).exists():
                        result = _enrich_gmt(dir_genes, gmt_path, db)
                        status["method"] = "local_gmt"
                    elif online:
                        result = _enrich_online(dir_genes, db, organism)
                        status["method"] = "enrichr_online"
                    else:
                        status["pathway_status"] = "unavailable"
                        status["significant_pathway_count"] = 0
                        status["failure_reason"] = "Online disabled and no local GMT available"
                        status_records.append(status)
                        continue

                    if result is not None and not result.empty:
                        result["cell_type"] = ct
                        if drug:
                            result["drug"] = drug
                        result["database"] = db
                        result["direction"] = direction
                        all_results.append(result)
                        status["pathway_status"] = "available"
                        status["significant_pathway_count"] = int(len(result))
                        status["tested_pathway_count"] = int(len(result))
                        status["failure_reason"] = ""
                    else:
                        status["pathway_status"] = "empty"
                        status["significant_pathway_count"] = 0
                        status["failure_reason"] = "No significant enrichment found"

                except Exception as e:
                    status["pathway_status"] = "error"
                    status["significant_pathway_count"] = 0
                    status["failure_reason"] = f"Enrichment error: {str(e)[:200]}"
                    logger.warning(f"Pathway enrichment failed for {group_label}/{db}/{direction}: {e}")

                status_records.append(status)

    pathway_df = pd.concat(all_results, ignore_index=True) if all_results else _empty_pathway_df()
    status_df = pd.DataFrame(status_records) if status_records else pd.DataFrame()

    logger.info(
        f"Pathway enrichment: {len(pathway_df)} results, "
        f"available={len(status_df[status_df['pathway_status']=='available']) if not status_df.empty else 0}, "
        f"empty={len(status_df[status_df['pathway_status']=='empty']) if not status_df.empty else 0}"
    )
    return pathway_df, status_df


def _clean_gene_list(genes: List[str]) -> List[str]:
    """Clean gene list: remove Ensembl IDs, duplicates, empties, and invalid symbols."""
    import re
    cleaned = []
    seen = set()
    ensg_pattern = re.compile(r'^ENSG\d+')
    for g in genes:
        g_str = str(g).strip()
        if not g_str:
            continue
        if ensg_pattern.match(g_str):
            continue  # Skip Ensembl IDs
        if g_str in seen:
            continue
        if len(g_str) > 50:  # Probably not a gene symbol
            continue
        if g_str.lower() in ('nan', 'none', 'null', ''):
            continue
        seen.add(g_str)
        cleaned.append(g_str)
    return cleaned


def _enrich_online(gene_list: List[str], database: str, organism: str) -> Optional[pd.DataFrame]:
    """Run gseapy enrichr online."""
    try:
        import gseapy as gp
    except ImportError:
        logger.warning("gseapy not installed")
        return None

    db_name = ENRICHR_DB_MAP.get(database, database)
    try:
        enr = gp.enrichr(gene_list=gene_list, gene_sets=db_name, organism=organism, outdir=None)
        if enr.results is not None and not enr.results.empty:
            return enr.results.copy()
        return None
    except Exception as e:
        raise


def _enrich_gmt(gene_list: List[str], gmt_path: str, database: str) -> Optional[pd.DataFrame]:
    """Run enrichment using local GMT file."""
    try:
        import gseapy as gp
    except ImportError:
        return None

    try:
        enr = gp.enrichr(gene_list=gene_list, gene_sets=gmt_path, outdir=None)
        if enr.results is not None and not enr.results.empty:
            return enr.results.copy()
        return None
    except Exception as e:
        raise


def compute_pathway_activity(pathway_df: pd.DataFrame, cell_type: str) -> float:
    """Compute pathway activity score = sum(-log10(padj)) for top 20 pathways."""
    subset = pathway_df[pathway_df["cell_type"] == cell_type]
    if subset.empty:
        return 0.0
    padj_col = None
    for col in ["Adjusted P-value", "P-value", "Adjusted P.value"]:
        if col in subset.columns:
            padj_col = col
            break
    if padj_col is None:
        return float(len(subset))
    top_n = min(20, len(subset))
    top = subset.nsmallest(top_n, padj_col)
    values = top[padj_col].clip(lower=1e-300)
    return float(np.sum(-np.log10(values)))


def _empty_pathway_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "cell_type", "database", "direction", "Term", "Overlap",
        "P-value", "Adjusted P-value", "Genes", "drug"
    ])
