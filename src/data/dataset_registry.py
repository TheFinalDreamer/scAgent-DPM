"""Dataset registry for tracking candidate perturbation datasets."""

from typing import Any, Dict, List


DATASET_REGISTRY: List[Dict[str, Any]] = []


def register_dataset(info: Dict[str, Any]) -> None:
    """Register a dataset candidate."""
    required_keys = {"name", "source", "url_or_accession", "format"}
    missing = required_keys - set(info.keys())
    if missing:
        raise ValueError(f"Dataset info missing required keys: {missing}")
    DATASET_REGISTRY.append(info)


def list_datasets() -> List[Dict[str, Any]]:
    return list(DATASET_REGISTRY)


def find_datasets(**criteria) -> List[Dict[str, Any]]:
    """Filter datasets by criteria, e.g. find_datasets(has_control=True, organism='human')."""
    results = DATASET_REGISTRY.copy()
    for key, value in criteria.items():
        results = [d for d in results if d.get(key) == value]
    return results


# --- Pre-registered perturbation dataset candidates ---
# These are literature-derived candidates; actual download requires network access.
# Status fields marked as "pending" until verified with real download.

CANDIDATE_DATASETS = [
    {
        "name": "scPerturb_combined",
        "paper": "Peidli et al., 2024, scPerturb: harmonized single-cell perturbation data",
        "source": "scPerturb database",
        "url_or_accession": "https://scperturb.org",
        "format": "h5ad",
        "organism": "human",
        "has_control": True,
        "has_treated": True,
        "has_cell_type_label": True,
        "has_batch": True,
        "n_cells": "varies by dataset",
        "n_genes": "varies by dataset",
        "suitable_experiments": ["D", "E", "F"],
        "status": "pending_download",
        "notes": "Harmonized collection; need to select specific sub-datasets with drug perturbations.",
    },
    {
        "name": "Perturb-seq_K562_GWAS",
        "paper": "Replogle et al., 2022, Mapping information-rich genotype-phenotype landscapes",
        "source": "GEO / scPerturb",
        "url_or_accession": "GSE169246",
        "format": "h5ad",
        "organism": "human",
        "has_control": True,
        "has_treated": True,
        "has_cell_type_label": False,
        "has_batch": True,
        "n_cells": ">2,500,000",
        "n_genes": "~20,000",
        "suitable_experiments": ["D"],
        "status": "pending_download",
        "notes": "CRISPR-based perturbations; currently not drug-based, useful for method validation.",
    },
    {
        "name": "sci-Plex3_cancer_drug_screen",
        "paper": "Srivatsan et al., 2020, Massively multiplex chemical transcriptomics",
        "source": "GEO",
        "url_or_accession": "GSE139944",
        "format": "h5ad",
        "organism": "human",
        "has_control": True,
        "has_treated": True,
        "has_cell_type_label": True,
        "has_batch": True,
        "n_cells": ">650,000",
        "n_genes": "~20,000",
        "suitable_experiments": ["D", "E", "F"],
        "status": "pending_download",
        "notes": "Cancer cell lines treated with 188 compounds at multiple doses. Strong candidate.",
    },
    {
        "name": "Drug_response_organoid_scRNA",
        "paper": "Various organoid drug screening studies",
        "source": "GEO / ArrayExpress",
        "url_or_accession": "TBD",
        "format": "h5ad",
        "organism": "human",
        "has_control": True,
        "has_treated": True,
        "has_cell_type_label": True,
        "has_batch": True,
        "n_cells": "varies",
        "n_genes": "varies",
        "suitable_experiments": ["D", "E"],
        "status": "pending_search",
        "notes": "Organoid drug response data with cell-type resolution; requires manual search.",
    },
    {
        "name": "Immune_stimulation_scRNA",
        "paper": "Various immune perturbation studies",
        "source": "GEO / CELLxGENE",
        "url_or_accession": "TBD",
        "format": "h5ad",
        "organism": "human",
        "has_control": True,
        "has_treated": True,
        "has_cell_type_label": True,
        "has_batch": True,
        "n_cells": "varies",
        "n_genes": "varies",
        "suitable_experiments": ["D", "E"],
        "status": "pending_search",
        "notes": "Immune stimulation as drug perturbation proxy; good for method validation.",
    },
]
