# scAgent-DPM 论文大纲

## Title

**scAgent-DPM: An Agentic Single-cell Analysis Framework for Drug Perturbation Mechanism Discovery via Adaptive Quality Control, Foundation Model Annotation and Dynamic State Modeling**

## Abstract

(To be written after results are finalized. Should include: background gap, system overview, key results, conclusion.)

---

## Introduction

1. Importance of single-cell drug perturbation transcriptomics
2. Current challenges in scRNA-seq drug perturbation analysis:
   - Manual/suboptimal QC parameter selection
   - Inconsistent cell-type annotation
   - Lack of integrated perturbation response scoring
   - Static analysis missing dynamic state transitions
   - Fragmented analysis workflows
3. Recent advances in:
   - Foundation models for single-cell data (scGPT, Geneformer)
   - Automated analysis pipelines (Scanpy, Seurat workflows)
   - Perturbation analysis tools (scPerturb, Augur, Mixscape)
4. Research gap: no end-to-end automated system integrating QC, annotation, perturbation scoring, and dynamic modeling
5. Our contributions:
   - scAgent-DPM: a fully automated agentic analysis framework
   - DPRS: a multi-dimensional drug perturbation response score
   - Lightweight agent planner with full reproducibility tracking
   - Systematic benchmark across multiple modules

---

## Methods

### System Overview

- Architecture diagram (Figure 1)
- Agent planner workflow (Figure 2)
- Module dependency graph
- Configuration and reproducibility design

### Data Ingestion and Preprocessing

- Supported input formats (h5ad, mtx, loom, csv)
- Automatic data field inspection
- Synthetic data generation for testing
- Standard preprocessing pipeline (normalization, HVG, PCA, UMAP)

### Adaptive Quality Control

- Multi-objective QC parameter search
- Composite scoring function
- Parameter space auto-detection from data distribution
- Baseline comparison: fixed QC, Scanpy default

### Foundation Model-Based Cell Annotation

- Unified annotation interface
- CellTypist baseline
- scGPT baseline
- scGPT-KDMT integration
- Confidence analysis and low-confidence cell detection

### Drug Perturbation Response Score (DPRS)

- Motivation for multi-dimensional scoring
- DPRS formula and component definitions:
  1. ProportionShift
  2. DEGIntensity
  3. PathwayActivity
  4. TrajectoryShift
  5. ConfidenceWeight
- Component normalization and weighting
- Missing component handling
- Drug-sensitive cell type identification

### Dynamic State Modeling

- Pseudotime trajectory inference
- Condition-specific trajectory comparison
- Trajectory shift quantification
- Mamba-LSTM interface for advanced dynamic modeling
- Wasserstein distance and Jensen-Shannon divergence metrics

### Agent Planner and Execution Engine

- Config-driven module selection
- Data field validation and auto-detection
- Step-by-step execution tracking
- Error handling and fallback mechanism
- Run manifest and execution graph generation

### Automated Report Generation

- Multi-format report generation (Markdown, HTML)
- Result table and figure integration
- Fallback result disclaimers
- Reproducibility metadata

### Experimental Setup and Baselines

- Datasets description
- Baseline methods for each module
- Evaluation metrics
- Statistical testing strategy

---

## Results

### Overview of scAgent-DPM

- System capabilities summary
- Execution workflow demonstration
- Module interaction visualization

### System Completion and Automation Performance

- End-to-end pipeline execution success rate
- Execution time breakdown by module
- Error recovery and fallback behavior

### Adaptive QC Improves Downstream Data Quality

- QC parameter search results
- Comparison with fixed QC: cell/gene retention, downstream clustering quality
- Parameter sensitivity analysis

### Foundation Model Annotation Improves Cell-Type Classification

- Annotation accuracy comparison: CellTypist vs scGPT vs scGPT-KDMT
- Confidence distribution analysis
- Low-confidence cell characterization
- Impact of QC method on annotation performance

### DPRS Identifies Drug-Responsive Cell Populations

- Proportion shift patterns
- DEG landscape across cell types
- Pathway enrichment summary
- DPRS ranking and drug-sensitive cell types
- Biological interpretation of top-ranked populations
- Comparison with single-dimensional metrics

### Dynamic Modeling Reveals Perturbation-Induced State Shifts

- Pseudotime trajectory comparison (control vs treated)
- Trajectory shift quantification
- Condition-specific state transition patterns
- Mamba-LSTM results (if available)

### Ablation Study

- Full system vs w/o adaptive QC
- Full system vs w/o scGPT-KDMT
- Full system vs w/o DPRS
- Full system vs w/o dynamic modeling
- Full system vs w/o agent planner
- Contribution of each module to overall performance

### Runtime and Reproducibility Analysis

- Runtime breakdown by module and dataset size
- GPU memory usage
- Cross-run consistency
- Cross-platform reproducibility

---

## Discussion

1. Summary of key findings
2. DPRS as a generalizable perturbation scoring framework
3. Advantages of agent-based automation for single-cell analysis
4. Limitations:
   - Dependence on model weight availability for foundation model modules
   - DPRS weight calibration may require domain-specific tuning
   - Current implementation focused on two-condition comparison
5. Comparison with existing tools
6. Future directions:
   - Multi-condition and dose-response analysis
   - Integration with spatial transcriptomics
   - Support for multi-omics perturbation data
   - Web-based interactive interface

---

## Data Availability

- Public datasets used are cited with accession numbers
- Synthetic demo data generation script included in repository
- Processed results are available in the supplementary materials

## Code Availability

- Source code available at: [GitHub repository URL — to be provided]
- Documentation and tutorials
- Docker/conda environment for reproducibility

## Supplementary Materials

- Supplementary Figures S1-SX
- Supplementary Tables S1-SX
- Full run manifests for all experiments
- Parameter search histories
- Extended pathway enrichment results
- Configuration files for all experiments
