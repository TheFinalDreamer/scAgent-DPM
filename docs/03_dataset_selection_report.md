# scAgent-DPM 数据集选择报告

## 检索策略

### 检索来源

1. **公共数据库**：GEO (NCBI Gene Expression Omnibus)、ArrayExpress、CELLxGENE
2. **扰动专用数据库**：scPerturb (https://scperturb.org)
3. **文献检索**：PubMed / Google Scholar 关键词检索
4. **预印本**：bioRxiv、medRxiv

### 检索关键词

- "drug perturbation scRNA-seq"
- "single-cell drug response"
- "Perturb-seq drug"
- "sci-Plex"
- "cancer drug screen single cell"
- "organoid drug response scRNA-seq"
- "immune stimulation single cell"

### 检索状态

当前阶段：检索计划已制定，数据集候选已登记。实际数据下载需在工作站/服务器上执行，且需要确认网络访问权限、数据存储空间和数据使用许可。

---

## 候选数据集清单

### 1. sci-Plex3 — 癌症药物筛选（高优先级）

| 字段 | 内容 |
|------|------|
| 数据集名称 | sci-Plex3 |
| 论文来源 | Srivatsan et al., 2020, Science |
| 数据库来源 | GEO: GSE139944 |
| 是否有 control/treated | 是（DMSO control + 188 种化合物处理） |
| 是否有 cell type label | 是（3 种癌症细胞系：A549, K562, MCF7） |
| 是否有 batch/sample | 是 |
| 细胞数 | > 650,000 |
| 基因数 | ~ 20,000 |
| 数据格式 | 原始数据为 SRA，已处理数据可转为 h5ad |
| 下载方式 | GEO / SRA toolkit / 预处理的 h5ad（需搜索） |
| 适合实验 | A, B, C, D, E, F |
| 风险与限制 | 数据量大，下载耗时长；细胞类型有限（仅 3 种细胞系）；处理前需要解复用和比对 |
| 当前状态 | pending_download |

### 2. scPerturb 统一扰动数据（高优先级）

| 字段 | 内容 |
|------|------|
| 数据集名称 | scPerturb combined |
| 论文来源 | Peidli et al., 2024, Nature Methods |
| 数据库来源 | scPerturb (https://scperturb.org) |
| 是否有 control/treated | 是（取决于子数据集选择） |
| 是否有 cell type label | 部分子数据集有 |
| 是否有 batch/sample | 是 |
| 细胞数 | 总计 > 10M（需选择药物相关子数据集） |
| 基因数 | 取决于子数据集 |
| 数据格式 | h5ad（统一处理后的格式） |
| 下载方式 | scPerturb 官网直接下载或通过 API |
| 适合实验 | A, B, C, D, E, F |
| 风险与限制 | 需要筛选药物扰动相关的子数据集；数据处理标准化程度可能不同 |
| 当前状态 | pending_download |

### 3. Perturb-seq — K562 GWAS 扰动（中优先级）

| 字段 | 内容 |
|------|------|
| 数据集名称 | Perturb-seq K562 GWAS |
| 论文来源 | Replogle et al., 2022, Cell |
| 数据库来源 | GEO: GSE169246 |
| 是否有 control/treated | 是 |
| 是否有 cell type label | 否（K562 为单一细胞系） |
| 是否有 batch/sample | 是 |
| 细胞数 | > 2,500,000 |
| 基因数 | ~ 20,000 |
| 数据格式 | h5ad / loom |
| 下载方式 | GEO / scPerturb |
| 适合实验 | D（方法验证） |
| 风险与限制 | 为 CRISPR 扰动而非药物扰动；单一细胞类型，限制了 DPRS 的验证；可用于方法学验证 |
| 当前状态 | pending_download |

### 4. 免疫刺激 scRNA-seq（中优先级）

| 字段 | 内容 |
|------|------|
| 数据集名称 | 免疫刺激单细胞数据集（多个候选） |
| 论文来源 | 待确定具体数据集后补充 |
| 数据库来源 | GEO / CELLxGENE |
| 是否有 control/treated | 是（刺激前后） |
| 是否有 cell type label | 通常有 |
| 是否有 batch/sample | 通常有 |
| 细胞数 | 取决于具体数据集（通常 5,000-100,000） |
| 基因数 | ~ 20,000 |
| 数据格式 | h5ad 或需转换 |
| 下载方式 | GEO / CELLxGENE |
| 适合实验 | D, E |
| 风险与限制 | 免疫刺激非传统意义药物扰动，需在论文中明确说明 |
| 当前状态 | pending_search |

### 5. 类器官药物响应 scRNA-seq（低优先级/探索性）

| 字段 | 内容 |
|------|------|
| 数据集名称 | 类器官药物处理 scRNA-seq |
| 论文来源 | 待补充 |
| 数据库来源 | GEO / ArrayExpress |
| 是否有 control/treated | 是 |
| 是否有 cell type label | 部分数据集有 |
| 是否有 batch/sample | 是 |
| 细胞数 | 不等 |
| 基因数 | ~ 20,000 |
| 数据格式 | 需转换 |
| 下载方式 | 需搜索确定 |
| 适合实验 | D, E |
| 风险与限制 | 需要手动筛选；类器官异质性高；数据质量和批次的标准化程度参差不齐 |
| 当前状态 | pending_search |

---

## 数据集选择策略与优先级

### 第一优先级（核心实验数据集）

- sci-Plex3（GSE139944）：药物种类多、细胞系清晰、实验设计规范、有 control
- scPerturb 中的药物扰动子数据集：数据已标准化、格式友好

### 第二优先级（验证数据集）

- 免疫刺激 scRNA-seq 数据集
- 独立来源的药物扰动数据集

### 第三优先级（扩展数据集）

- 类器官药物响应数据
- 患者来源样本的药物响应数据

---

## 数据集检索模板

后续搜索中，每个新候选数据集按以下模板登记：

```yaml
- name: "数据集简称"
  paper: "第一作者 et al., 年份, 期刊"
  source: "GEO / ArrayExpress / CELLxGENE / 其他"
  url_or_accession: "accession number or URL"
  format: "h5ad / loom / mtx / csv"
  organism: "human / mouse"
  has_control: true/false
  has_treated: true/false
  has_cell_type_label: true/false
  has_batch: true/false
  n_cells: "数量"
  n_genes: "数量"
  drug_type: "small molecule / antibody / cytokine / CRISPR / other"
  suitable_experiments: ["A", "B", "C", "D", "E", "F"]
  status: "pending_download / downloaded / processed / failed"
  notes: "补充说明"
```

## 注意事项

1. 所有数据集下载前需确认使用许可和数据共享政策。
2. 数据下载后不得重新分发，仅在本项目内使用。
3. 下载的数据文件存放于服务器指定目录，不在本地存储大规模原始数据。
4. 每个数据集处理完成后记录处理脚本和参数，确保可复现。
5. 若所有候选数据集均无法获取，考虑使用公开的免疫细胞 atlas 数据（如 PBMC）进行 synthetic perturbation 模拟。
