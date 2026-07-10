# scAgent-DPM 实验结果留存规范

## 一、总则

每次实验必须保存完整的输入、中间结果、最终结果和执行记录，确保实验结果可追溯、可复现、可审计。失败实验同样需要记录，以便问题排查。

---

## 二、文件命名规则

### 2.1 运行目录

```
results/<experiment_type>/<YYYYMMDD>_<HHMMSS>_<run_description>/
```

示例：
```
results/qc/20240601_143025_adaptive_vs_fixed/
results/perturbation/20240603_091200_sci-plex3_full/
```

### 2.2 输出文件

使用固定的语义化文件名，避免版本号后缀：

| 文件 | 命名 |
|------|------|
| 数据摘要 | `data_summary.json` |
| QC 报告 | `qc_report.json` |
| 细胞注释 | `cell_annotation.csv` |
| 预测置信度 | `prediction_confidence.csv` |
| 低置信度细胞 | `low_confidence_cells.csv` |
| 细胞比例偏移 | `proportion_shift.csv` |
| DEG 结果 | `deg_results.csv` |
| 通路富集 | `pathway_results.csv` |
| DPRS 评分 | `dprs_scores.csv` |
| 药物敏感细胞 | `drug_sensitive_cell_types.csv` |
| 扰动摘要 | `perturbation_summary.json` |
| 伪时间 | `pseudotime.csv` |
| 轨迹偏移 | `trajectory_shift.csv` |
| 运行清单 | `run_manifest.json` |
| 执行图 | `execution_graph.json` |
| 可复现元数据 | `reproducibility_metadata.json` |
| Markdown 报告 | `report.md` |
| HTML 报告 | `report.html` |

### 2.3 日志命名

```
logs/<YYYYMMDD>_<HHMMSS>_<run_name>.log
```

---

## 三、实验结果存储结构

```
results/
├── demo/
│   └── YYYYMMDD_HHMMSS_demo/
│       ├── data_summary.json
│       ├── qc_report.json
│       ├── cell_annotation.csv
│       ├── dprs_scores.csv
│       ├── report.md
│       ├── report.html
│       └── run_manifest.json
├── qc/
│   └── YYYYMMDD_HHMMSS_benchmark/
│       ├── adaptive_qc_stats.json
│       ├── baseline_comparison.csv
│       └── qc_comparison.png
├── annotation/
│   └── YYYYMMDD_HHMMSS_benchmark/
│       ├── annotation_comparison.csv
│       ├── confidence_distribution.png
│       └── annotation_summary.json
├── perturbation/
│   └── YYYYMMDD_HHMMSS_<dataset>/
│       ├── dprs_scores.csv
│       ├── proportion_shift.csv
│       ├── deg_results.csv
│       ├── pathway_results.csv
│       ├── drug_sensitive_cell_types.csv
│       ├── perturbation_summary.json
│       └── figures/
├── dynamics/
│   └── YYYYMMDD_HHMMSS_<dataset>/
│       ├── pseudotime.csv
│       ├── trajectory_shift.csv
│       ├── trajectory_shift.png
│       └── dynamic_state_report.md
├── ablation/
│   └── YYYYMMDD_HHMMSS/
│       ├── ablation_metrics.csv
│       ├── ablation_summary.md
│       └── ablation_plot.png
└── final_summary/
    └── FINAL_RESULTS_SUMMARY.md
```

---

## 四、必须保存的内容

### 4.1 每次运行必须保存

- [ ] 完整配置文件快照
- [ ] 数据来源信息（路径或生成参数）
- [ ] 所有模块的输出文件
- [ ] run_manifest.json
- [ ] execution_graph.json
- [ ] 运行日志（包含所有 WARNING 和 ERROR）
- [ ] reproducibility_metadata.json
- [ ] Fallback 状态标记

### 4.2 实验完成后必须保存

- [ ] 所有对比实验的结果汇总表
- [ ] 关键图表（PNG ≥ 300 dpi + PDF 矢量图）
- [ ] 统计检验结果
- [ ] 实验环境信息（conda list 输出）

---

## 五、图表保存规则

### 5.1 图表格式

- 论文用图：PDF（矢量）+ PNG（300 dpi）
- 报告用图：PNG（150 dpi，嵌入 HTML）
- 中间分析图：PNG（150 dpi）

### 5.2 图表命名

```
<experiment>_<plot_type>.png
<experiment>_<plot_type>.pdf
```

示例：
```
dprs_ranking.png
proportion_comparison.pdf
umap_cell_types.png
```

### 5.3 图表存储

- 实验输出目录下的 `figures/` 子目录
- 同时复制一份到 `manuscript_assets/figures/`（用于论文）

---

## 六、中间结果保存规则

### 6.1 需要保存的中间结果

- 处理后的 AnnData 对象（可选，文件较大时仅保留路径记录）
- QC 前后的基本统计
- 参数搜索历史
- 注释方法的中间预测

### 6.2 不需要保存的中间结果

- 临时解压文件
- 过大的中间矩阵（可以从源码重新计算）
- 已包含在最终结果中的冗余副本

---

## 七、失败实验记录

失败实验同样需要生成记录：

```json
{
  "experiment_name": "...",
  "status": "failed",
  "failure_module": "annotation",
  "failure_reason": "scGPT model weights not found at /path/to/weights.pt",
  "failure_timestamp": "...",
  "recovery_suggestion": "Download weights or set fallback_allowed=true",
  "partial_outputs": ["data_summary.json", "qc_report.json"]
}
```

失败实验的输出存放在 `results/failed/` 目录，不与其他成功实验混合。

---

## 八、服务器结果回传

### 8.1 回传内容

- 所有最终结果文件（非大型中间文件）
- 日志文件
- 图表文件
- 汇总报告

### 8.2 回传方式

```bash
# 压缩结果目录
tar -czf results_YYYYMMDD.tar.gz results/<experiment>/

# 回传到本地（根据实际连接方式选择）
scp user@server:/data/sc/scAgent_DPM/results_YYYYMMDD.tar.gz ./

# 或使用 rsync
rsync -avz user@server:/data/sc/scAgent_DPM/results/<experiment>/ ./results/<experiment>/
```

### 8.3 不回传的内容

- 大型原始数据文件（> 1 GB）
- conda 环境目录
- 临时文件
- 缓存的模型权重（除非需要归档）

---

## 九、投稿前冻结

投稿前，将所有最终实验结果和代码冻结为一个不可变的归档版本：

```bash
# 冻结代码
git archive --format=tar.gz --output=scAgent-DPM_v1.0.tar.gz HEAD

# 冻结结果
tar -czf scAgent-DPM_results_final.tar.gz results/final_summary/ manuscript_assets/

# 记录文件校验和
sha256sum scAgent-DPM_v1.0.tar.gz > checksums.txt
sha256sum scAgent-DPM_results_final.tar.gz >> checksums.txt
```

---

## 十、检查清单

在每次实验前确认：
- [ ] 配置文件已保存
- [ ] 数据路径正确
- [ ] 输出目录不存在或为空（避免覆盖）
- [ ] 磁盘空间充足（至少预留 5 GB）

在每次实验后确认：
- [ ] run_manifest.json 已生成
- [ ] 所有预期输出文件已生成
- [ ] 无未预期的 fallback
- [ ] 日志无遗漏的 ERROR
- [ ] 图表可正常打开
