# scAgent-DPM 系统设计报告

## 一、总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Planner                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Config   │  │ Data     │  │ Module   │  │ Reproducibility│  │
│  │ Loader   │→ │ Inspector│→ │ Selector │→ │ Tracker       │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Data Ingestion │  │  Adaptive QC    │  │  Preprocessing  │
│  h5ad/mtx/loom  │→ │  multi-obj opt  │→ │  norm/HVG/PCA   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Annotation     │  │  Perturbation   │  │  Dynamics       │
│  CellTypist/    │  │  DPRS/DEG/      │  │  Pseudotime/    │
│  scGPT/scGPT-   │  │  Pathway/       │  │  Mamba-LSTM     │
│  KDMT           │  │  Proportion     │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Reporting      │
                    │  Markdown/HTML  │
                    │  Figures/Tables │
                    └─────────────────┘
```

## 二、模块详细说明

### 2.1 Data Ingestion Layer

**文件**：`src/data/loaders.py`, `converters.py`, `preprocessing.py`, `dataset_registry.py`

**功能**：
- 支持 h5ad、mtx+barcodes+features、loom、csv 等输入格式
- 自动检测数据字段（condition_key, batch_key, cell_type_key）
- 自动检测线粒体基因前缀（MT- / mt-）
- 无输入文件时自动生成 synthetic demo 数据

**输出**：
- 标准化 AnnData 对象
- 数据摘要 JSON（data_summary.json）
- 数据字段检查报告

### 2.2 Adaptive QC Layer

**文件**：`src/qc/adaptive_qc.py`, `qc_metrics.py`, `qc_report.py`

**功能**：
- 多目标参数搜索（min_genes, max_mt_pct 等）
- 综合评分函数（细胞保留率 + 基因保留率 + MT 控制）
- 支持固定阈值 QC 作为 baseline
- 记录参数搜索历史

**算法**：
1. 从数据分布自动生成参数搜索边界
2. 随机采样参数组合，评估综合 QC 得分
3. 返回最优参数组合和过滤后的 AnnData

### 2.3 Foundation Model Annotation Layer

**文件**：`src/annotation/celltypist_runner.py`, `scgpt_runner.py`, `scgpt_kdmt_runner.py`, `confidence.py`, `annotation_metrics.py`

**功能**：
- 统一注释接口，支持三种方法
- 自动检测模型可用性，必要时 fallback
- 注释置信度分析和低置信度细胞检测
- 注释性能评估

**Fallback 机制**：
- 若模型/权重不可用 → 生成 mock 预测
- 所有 fallback 结果在日志和报告中明确标记
- Fallback 标志写入 run_manifest.json

### 2.4 Drug Perturbation Response Score (DPRS)

**文件**：`src/perturbation/dprs.py`, `deg.py`, `pathway.py`, `proportion_shift.py`, `perturbation_report.py`

**DPRS 公式**：
```
DPRS(c) = w1 * ProportionShift(c) + w2 * DEGIntensity(c)
        + w3 * PathwayActivity(c) + w4 * TrajectoryShift(c)
        + w5 * ConfidenceWeight(c)
```

**组件说明**：
- **ProportionShift**：control vs treated 细胞比例变化的标准化值
- **DEGIntensity**：该细胞类型内差异表达基因的综合强度（mean|logFC| × -log10(padj)）
- **PathwayActivity**：通路富集显著性的综合得分
- **TrajectoryShift**：药物扰动导致的伪时间轨迹偏移量
- **ConfidenceWeight**：注释置信度的细胞类型平均权重

**缺失组件处理**：
- 若某组件数据不可用，该组件贡献为 0
- 有效权重重新归一化
- 结果中记录 available_components 和 missing_components

### 2.5 Dynamic State Modeling Layer

**文件**：`src/dynamics/pseudotime.py`, `sequence_builder.py`, `mamba_lstm_interface.py`, `trajectory_shift.py`, `dynamic_metrics.py`

**功能**：
- 伪时间分析（scanpy DPT）
- 条件间轨迹偏移量化
- Mamba-LSTM 模型接口（当模型可用时）

**双轨策略**：
- Track 1（始终可用）：Pseudotime + trajectory shift baseline
- Track 2（模型可用时）：Mamba-LSTM 序列建模 + 轨迹偏移预测

### 2.6 Agent Planner & Executor

**文件**：`src/agent/planner.py`, `executor.py`, `state.py`, `validators.py`

**功能**：
- 读取配置，检测数据字段
- 决定模块执行顺序
- 记录每步输入/输出/参数/状态
- 失败时自动重试或降级
- 生成 execution_graph.json 和 run_manifest.json

**执行状态**：
- `success`：模块正常完成
- `failure`：模块执行失败
- `fallback`：使用降级/模拟方式完成
- `skipped`：模块被配置跳过

### 2.7 Reporting Layer

**文件**：`src/reporting/markdown_report.py`, `html_report.py`, `figure_exporter.py`, `tables.py`

**功能**：
- Markdown 格式报告
- HTML 格式报告（含样式）
- 图片导出（PNG + PDF）
- 结果表格格式化

**报告区分**：
- 真实实验：正常结果展示
- Fallback 结果：明确标注 "NOT for publication"
- 接口测试：标注为 interface test

---

## 三、数据流

```
Input (h5ad)
  → AnnData (raw)
  → [QC] AnnData (filtered)
  → [Preprocess] AnnData (normalized, HVG, PCA, UMAP)
  → [Annotation] AnnData.obs + cell_annotation.csv
  → [Perturbation] proportion_df, deg_df, pathway_df
  → [Dynamics] pseudotime_df, trajectory_shift
  → [DPRS] dprs_df, drug_sensitive
  → [Reporting] report.md, report.html
```

## 四、文件流

```
input.h5ad
  → results/<run_name>/
      ├── data_summary.json
      ├── qc_report.json
      ├── cell_annotation.csv
      ├── prediction_confidence.csv
      ├── low_confidence_cells.csv
      ├── proportion_shift.csv
      ├── deg_results.csv
      ├── pathway_results.csv
      ├── dprs_scores.csv
      ├── drug_sensitive_cell_types.csv
      ├── perturbation_summary.json
      ├── pseudotime.csv
      ├── report.md
      ├── report.html
      ├── run_manifest.json
      ├── execution_graph.json
      └── reproducibility_metadata.json
```

## 五、配置流

```
configs/default.yaml (默认配置)
  → 命令行 --config 覆盖
  → Config 对象加载和验证
  → PipelineState 记录 config_snapshot
  → reproducibility_metadata.json 保存配置
```

## 六、日志流

```
logs/<run_name>.log
  → 主日志：所有模块日志（DEBUG 级别写入文件）
  → 控制台：INFO 级别
  → 错误日志：ERROR 级别含完整 traceback
  → run_manifest.json：结构化执行记录
```

## 七、错误处理与 Fallback 机制

### 错误分级

1. **致命错误**：数据文件不存在、必需字段缺失 → 终止流程，记录错误
2. **可恢复错误**：模型加载失败、可选模块执行失败 → 记录错误，尝试 fallback
3. **警告**：非理想但可继续的情况 → 记录警告，继续执行

### Fallback 策略

| 场景 | Fallback 行为 | 标记 |
|------|--------------|------|
| 无输入数据 | 生成 synthetic 数据 | DEMO/FALLBACK |
| 注释模型不可用 | Mock 预测 | FALLBACK annotation |
| Mamba-LSTM 不可用 | Pseudotime baseline | FALLBACK dynamics |
| Pathway 数据库不可用 | 跳过 pathway 组件 | missing_components |
| 无 cell type label | 仅运行比例偏移（不分组） | reduced analysis |

### Fallback 标记链

- 日志中：WARNING 级别 + "FALLBACK" 关键词
- run_manifest.json：`is_fallback: true`
- 报告中：红色/黄色警告块 + "NOT for publication"
- DPRS metadata：`missing_components` 列表

---

## 八、服务器运行策略

### 环境
- 路径：`/data/sc/scAgent_DPM`（默认，可配置）
- 环境：conda env `scagent-dpm`
- Python：3.10
- GPU：NVIDIA GPU（用于 scGPT 和 Mamba-LSTM 推理）

### 运行方式
- 短期任务：直接运行
- 长期任务：tmux 会话或 nohup 后台运行
- 批量实验：`bash scripts/server_run_all.sh`

### 不做什么
- 不在本地 Windows 上跑大实验
- 不暴露服务器端口到公网
- 不要求 sudo 权限
- 不覆盖现有 scGPT-KDMT 或 scLifeMamba 项目
