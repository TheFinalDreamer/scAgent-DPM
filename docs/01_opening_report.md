# 开题报告

## 题目

面向药物干预机制解析的单细胞智能分析体：融合自适应质量控制、基础模型注释与动态状态建模的自动化分析系统

英文题目：scAgent-DPM: An Agentic Single-cell Analysis Framework for Drug Perturbation Mechanism Discovery via Adaptive Quality Control, Foundation Model Annotation and Dynamic State Modeling

---

## 一、研究背景与意义

### 1.1 单细胞药物扰动转录组学的发展

单细胞 RNA 测序技术的快速发展使得在单细胞分辨率下研究药物对转录组的扰动效应成为可能。Perturb-seq、sci-Plex、CROP-seq 等高通量扰动筛选技术已经产生大规模药物扰动单细胞数据集，为系统性解析药物作用机制提供了数据基础。然而，从原始数据到生物学解释的分析过程涉及质量控制、细胞类型注释、差异表达分析、通路富集分析和动态建模等多个环节，现有方法在自动化程度、方法系统性和结果可复现性方面存在明显不足。

### 1.2 核心挑战

1. **质量控制的主观性**：传统固定阈值 QC 方法依赖于人工经验设定参数，难以适应不同数据集的质量特征。
2. **细胞注释的一致性**：人工注释耗时且主观，不同参考数据集和方法可能导致不一致的注释结果。
3. **扰动效应的多维性**：药物扰动同时影响细胞比例、基因表达、通路活性和细胞状态，缺乏整合这些多维信息的统一量化框架。
4. **动态信息的丢失**：静态差异表达分析无法捕获扰动诱导的细胞状态动态转变。
5. **分析流程的碎片化**：现有工具通常仅覆盖单一分析环节，缺乏端到端的自动化系统。

### 1.3 研究意义

构建一个集成自适应质量控制、基础模型注释、药物扰动响应评分和动态状态建模的自动化单细胞分析系统，对于加速药物作用机制研究、提高分析结果的可复现性和标准化药物扰动数据分析流程具有重要的科学意义和应用价值。

---

## 二、国内外研究现状

### 2.1 单细胞质量控制方法

传统 QC 方法（如 Scanpy 的 filter_cells/filter_genes）使用固定阈值进行细胞和基因过滤。近年来，自适应 QC 方法开始出现，如 scQcut 基于数据分布自动确定阈值，SCTK 提供交互式 QC 参数探索。但系统性的多目标自适应 QC 优化方法仍较为缺乏。

### 2.2 单细胞注释方法

基于标记基因的自动注释方法（如 CellTypist、SingleR）已广泛使用。基于深度学习的注释方法（如 scBERT、scGPT、TOSICA）利用预训练模型提高了注释准确性。研究组前期提出的 scGPT-KDMT 方法通过知识蒸馏和多任务学习进一步提升了注释性能。

### 2.3 药物扰动分析方法

差异表达分析（DESeq2、Wilcoxon rank-sum）和通路富集分析（GSEA、Enrichr）是药物扰动分析的标准方法。Augur、scPerturb 等工具提供了扰动响应评分，但通常仅基于单一维度。Mixscape 结合了遗传扰动和表达变化。整合多维度信息的药物扰动响应综合评分框架尚属空白。

### 2.4 动态建模方法

RNA velocity 和伪时间分析（Monocle、Slingshot、scVelo）可推断细胞状态转变方向。基于深度学习的动态建模方法（如 Mamba-LSTM、scTour）能够从静态快照数据中学习动态规律。

### 2.5 自动化分析系统

Seurat、Scanpy 和 scVI-tools 提供了基础的自动化流程框架。Cell Ranger、STARsolo 等上游工具提供了标准化的数据预处理。但面向药物扰动分析全流程的自动化系统尚未出现。

---

## 三、现有问题分析

1. QC 参数选择缺乏系统性优化，固定阈值法无法适应数据异质性。
2. 细胞注释方法之间缺乏公平对比框架，注释置信度信息未被下游分析充分利用。
3. 缺乏整合细胞比例变化、差异表达强度、通路活性和状态转变的多维度扰动评分。
4. 静态分析无法捕获药物扰动诱导的动态生物学过程。
5. 从数据到报告的全流程缺乏自动化、可复现的工程实现。

---

## 四、研究目标

1. 构建面向药物扰动机制解析的端到端自动化单细胞分析系统（scAgent-DPM）。
2. 提出整合多维度信息的药物扰动响应评分（DPRS）框架。
3. 设计轻量级智能体规划器实现全流程自动化与可复现性保障。
4. 通过系统性的实验验证各模块的性能和系统的整体有效性。

---

## 五、研究内容

### 5.1 自适应质量控制模块

基于多目标优化策略的自适应 QC 参数搜索算法，自动确定最优过滤阈值，平衡细胞保留率、基因保留率和线粒体基因比例控制。

### 5.2 基础模型细胞注释模块

构建统一注释接口，支持 CellTypist 基线、scGPT 基线和 scGPT-KDMT 三种方法，提供注释置信度评估和低置信度细胞检测。

### 5.3 药物扰动响应评分（DPRS）

提出 DPRS 框架：
```
DPRS(c) = w1·ProportionShift(c) + w2·DEGIntensity(c) + w3·PathwayActivity(c)
        + w4·TrajectoryShift(c) + w5·ConfidenceWeight(c)
```
整合细胞比例变化、差异表达强度、通路活性、轨迹偏移和注释置信度五个维度。

### 5.4 动态状态建模模块

构建伪时间分析与 Mamba-LSTM 双轨动态建模接口，定量评估扰动诱导的细胞状态转变。

### 5.5 智能体规划器与执行引擎

设计轻量级 Agent Planner，自动检测数据字段，决定模块执行顺序，记录每步输入输出和参数，生成执行图谱和 run manifest。

### 5.6 自动报告生成

自动生成 Markdown 和 HTML 格式的分析报告，区分真实实验、接口测试和 fallback 结果。

---

## 六、技术路线

```
Raw scRNA-seq → Data Ingestion → Adaptive QC → Preprocessing
→ Cell Annotation → Drug Perturbation Analysis (DPRS)
→ Dynamic State Modeling → Agent Planner → Automated Report
```

主要技术栈：Python、PyTorch、Scanpy、AnnData、CellTypist、scGPT、Mamba-LSTM

---

## 七、创新点

1. **DPRS 框架**：首次提出整合五维度信息的药物扰动响应综合评分方法。
2. **自适应 QC 集成**：将自适应质量控制作为自动化流程的标准前序模块。
3. **基础模型注释集成**：首次在药物扰动分析流程中集成基础模型细胞注释及其置信度信息。
4. **Agent Planner**：设计轻量级智能体规划器实现全流程自动化与完整审计追踪。
5. **Fallback 透明机制**：所有降级/模拟结果均明确标记，确保研究诚信。

---

## 八、实验设计

详见 `docs/02_experimental_design_report.md`。实验体系包括：

- A. System Completion Test（系统完整性测试）
- B. Adaptive QC Benchmark（QC 对比实验）
- C. Cell Annotation Benchmark（注释对比实验）
- D. Drug Perturbation Response Analysis（药物扰动分析）
- E. Dynamic State Modeling Evaluation（动态建模评估）
- F. Ablation Study（消融实验）
- G. Reproducibility and Runtime Analysis（可复现性与运行效率分析）

---

## 九、可行性分析

### 9.1 技术可行性

- 研究组在单细胞质量控制（第一篇）、基础模型注释（第二篇）和动态建模（第三篇）方面已有成熟技术积累。
- 所需计算资源（GPU 服务器、conda 环境）已有配置经验。
- 公开药物扰动单细胞数据集（scPerturb、Perturb-seq、sci-Plex）提供充足实验数据。

### 9.2 时间可行性

- 项目骨架和 demo 流程可在 2 周内完成。
- 各模块独立开发可并行推进。
- 真实数据集实验视数据获取速度，预计 4-8 周完成。

### 9.3 风险可控性

- 若真实模型权重缺失，系统设计已包含明确的 fallback 机制和标识体系。
- 若特定数据集无法获取，已建立备选数据集候选清单。
- 模块化设计确保单个模块的延迟不影响其他模块的开发测试。

---

## 十、预期成果

1. **软件系统**：scAgent-DPM 完整分析系统（含源代码、文档和测试）。
2. **学术论文**：SCI 二区及以上期刊论文 1 篇。
3. **算法方法**：DPRS 药物扰动响应评分框架。
4. **实验数据**：系统性基准测试结果和消融实验数据。

---

## 十一、进度安排

| 阶段 | 时间 | 内容 |
|------|------|------|
| 项目初始化 | 第1周 | 项目结构、配置、基础模块、demo pipeline |
| 文档写作 | 第1-2周 | 开题报告、实验设计、系统设计、可复现性方案 |
| 模块完善 | 第2-4周 | QC、注释、扰动、动态各模块完善 |
| 服务器部署 | 第3-4周 | 环境配置、数据集下载、真实实验启动 |
| 实验运行 | 第4-8周 | 基准测试、对比实验、消融实验 |
| 结果整理 | 第8-10周 | 结果收集、统计分析、图表制作 |
| 论文写作 | 第10-14周 | 论文初稿、修改、投稿 |

---

## 十二、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 真实模型权重不可用 | 中 | 中 | 使用 fallback 完成接口测试，标注后使用替代方法 |
| 目标数据集无法获取 | 低 | 中 | 已有 5 个以上候选数据集，逐一尝试 |
| 服务器资源不足 | 低 | 高 | 使用 tmux 后台运行，评估云端 GPU 备选方案 |
| DPRS 权重需要调整 | 中 | 低 | 通过消融实验验证各组件贡献，支持配置化调整 |
| 论文被拒稿 | 中 | 高 | 准备多个目标期刊，根据审稿意见修改 |

---

## 参考文献（占位）

[1] Wolf, F.A., et al. (2018). SCANPY: large-scale single-cell gene expression data analysis. Genome Biology.
[2] Domínguez Conde, C., et al. (2022). Cross-tissue immune cell analysis reveals tissue-specific features in humans. Science.
[3] Cui, H., et al. (2024). scGPT: toward building a foundation model for single-cell multi-omics. Nature Methods.
[4] Peidli, S., et al. (2024). scPerturb: harmonized single-cell perturbation data. Nature Methods.
[5] Srivatsan, S.R., et al. (2020). Massively multiplex chemical transcriptomics at single-cell resolution. Science.
[6] Replogle, J.M., et al. (2022). Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq. Cell.
[7] [前三篇相关论文占位 — 待补充完整引用]

注：最终版将补充完整参考文献列表。
