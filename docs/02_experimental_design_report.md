# scAgent-DPM 实验设计报告

## 一、总体实验目标

系统性验证 scAgent-DPM 系统在药物扰动单细胞数据分析中的有效性、自动化程度和可复现性。实验设计覆盖系统完整性、模块性能、对比基准和消融分析四个层面。

---

## 二、数据集选择标准

### 2.1 入选标准

- 包含 control 和 treated（药物处理）两组条件
- 具有细胞类型标签（人工注释或已知 marker）
- 数据格式为 h5ad 或可转换为 AnnData
- 细胞数 > 1,000
- 基因数 > 5,000
- 优先选择公开可下载的数据集

### 2.2 数据集候选

详见 `docs/03_dataset_selection_report.md`。初选数据集包括：
1. sci-Plex3 癌症药物筛选数据（GSE139944）
2. scPerturb 统一扰动数据
3. Perturb-seq 数据（GSE169246）
4. 免疫刺激 scRNA-seq 数据
5. 类器官药物响应 scRNA-seq 数据

### 2.3 数据集分组

- **Demo 数据集**：synthetic 或小型子采样数据，用于功能验证
- **主要实验数据集**：1-2 个高质量药物扰动数据集
- **验证数据集**：1 个独立数据集用于跨数据集验证

---

## 三、实验分组

### A. System Completion Test（系统完整性测试）

**目标**：验证完整流程能否自动执行，所有模块输入输出是否正确。

**输入**：synthetic AnnData（1000 cells × 2000 genes）或小型 demo h5ad

**输出验证项**：
- [ ] QC summary 生成
- [ ] 预处理完成
- [ ] 注释结果生成（cell_annotation.csv）
- [ ] DPRS 分数表生成
- [ ] 动态建模结果生成
- [ ] run_manifest.json 生成
- [ ] execution_graph.json 生成
- [ ] Markdown 报告生成
- [ ] HTML 报告生成
- [ ] Fallback 标记是否正确写入

**注意**：synthetic 数据结果不得作为论文真实性能结果。

### B. Adaptive QC Benchmark

**目标**：验证自适应 QC 相对于固定阈值 QC 的优势。

**对比方法**：
1. Fixed QC（min_genes=200, max_mt_pct=20）
2. Scanpy default-like QC（min_genes=200, min_cells=3, max_mt_pct=20）
3. Adaptive QC（本方法）

**评价指标**：
- Retained cell ratio（细胞保留率）
- Retained gene ratio（基因保留率）
- Mean mitochondrial ratio after QC（QC 后平均线粒体比例）
- Downstream clustering silhouette score（下游聚类轮廓系数）
- Annotation stability（注释稳定性：不同 QC 后注释一致性）
- Composite QC score（综合 QC 评分）

**实验设置**：
- 在 2 个以上数据集上运行
- 记录参数搜索历史和最优参数
- 生成 QC 前后对比图

### C. Cell Annotation Benchmark

**目标**：评估不同注释方法在药物扰动数据上的性能。

**对比方法**：
1. CellTypist（baseline，使用内置 Immune_All 模型）
2. scGPT（baseline，使用预训练权重）
3. scGPT-KDMT（研究组前期方法）
4. scAgent-DPM annotation module（集成上述方法 + 置信度分析）

**评价指标**：
- Accuracy
- Macro-F1
- Weighted-F1
- Precision（macro）
- Recall（macro）
- Confidence calibration error
- Low-confidence detection rate

**实验设置**：
- 使用具有 ground truth 细胞类型标签的数据集
- 记录每种方法的运行时间和 GPU 内存使用
- 分析低置信度细胞的生物学特征

**注意**：若 scGPT 或 scGPT-KDMT 模型权重不可用，对应方法标记为 fallback，不参与性能对比。

### D. Drug Perturbation Response Analysis

**目标**：验证 DPRS 框架识别药物敏感细胞群体的有效性。

**分析内容**：
1. **细胞比例偏移分析**：control vs treated 各细胞类型比例变化
2. **差异表达分析**：每种细胞类型内的 DEG
3. **通路富集分析**：DEG 的通路富集
4. **DPRS 计算**：综合五维度评分
5. **药物敏感群体识别**：高 DPRS 细胞类型

**输出验证**：
- proportion_shift.csv（细胞比例偏移表）
- deg_results.csv（差异表达结果）
- pathway_results.csv（通路富集结果）
- dprs_scores.csv（DPRS 评分表）
- drug_sensitive_cell_types.csv（药物敏感细胞类型）
- perturbation_summary.json（扰动分析摘要）

**DPRS 组件可用性记录**：
- 记录每个组件的可用性状态（available / missing / fallback）
- 若 pathway 或 trajectory 组件缺失，DPRS 仅基于可用组件计算
- 报告中必须明确列出缺失组件

### E. Dynamic State Modeling Evaluation

**目标**：评估动态建模方法捕获药物扰动诱导状态转变的能力。

**对比方法**：
1. Pseudotime baseline（scanpy DPT）
2. Mamba-LSTM（研究组前期方法，若模型可用）

**评价指标**：
- Trajectory shift score（伪时间分布偏移量）
- State transition consistency（状态转变一致性）
- Perturbation ranking stability（扰动排序稳定性）
- Wasserstein distance between conditions

**实验设置**：
- 构建 control 和 treated 的伪时间轨迹
- 计算条件间的轨迹偏移
- 若 Mamba-LSTM 模型可用，进行序列建模对比

### F. Ablation Study（消融实验）

**目标**：量化各模块对系统整体性能的贡献。

**消融条件**：
1. Full scAgent-DPM（完整系统）
2. w/o Adaptive QC（替换为固定阈值 QC）
3. w/o scGPT-KDMT（替换为 CellTypist）
4. w/o DPRS（仅使用单一 DEG 指标）
5. w/o Dynamic Modeling（移除轨迹偏移组件）
6. w/o Agent Planner（手动顺序执行）

**评价指标**：
- 药物敏感细胞识别的一致性
- 结果可复现性评分
- 运行时间
- 人工干预次数

**输出**：
- ablation_metrics.csv
- ablation_summary.md
- ablation_plot.png

### G. Reproducibility and Runtime Analysis

**目标**：验证系统的可复现性和运行效率。

**测试内容**：
- 同一数据集、同一 seed 下重复运行 3 次，输出一致性
- 不同 seed 下运行，结果稳定性
- 记录各模块运行时间
- 记录 GPU 内存使用峰值
- 记录磁盘使用

---

## 四、评价指标汇总

| 实验组 | 主要指标 | 次要指标 |
|--------|----------|----------|
| A. System Completion | 所有模块成功执行 | 错误恢复 |
| B. QC Benchmark | Composite QC score | Silhouette score |
| C. Annotation | Weighted-F1 | Confidence calibration |
| D. Perturbation | DPRS ranking stability | Biological consistency |
| E. Dynamics | Trajectory shift score | Wasserstein distance |
| F. Ablation | Drug-sensitive overlap | Runtime |
| G. Reproducibility | Output checksum match | Runtime variance |

---

## 五、统计检验策略

- 两组比较：Wilcoxon rank-sum test 或 t-test（视数据分布）
- 多组比较：Friedman test + post-hoc Nemenyi test
- 相关性分析：Spearman rank correlation
- 多重检验校正：Benjamini-Hochberg FDR
- 显著性水平：α = 0.05（除非另有说明）

---

## 六、结果留存规范

详见 `docs/06_result_retention_protocol.md`。每次实验必须保存：
- 输入配置
- 完整日志
- 中间结果
- 最终结果
- run_manifest.json
- reproducibility_metadata.json
