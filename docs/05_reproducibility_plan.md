# scAgent-DPM 可复现性计划

## 一、环境可复现

### 1.1 Conda 环境

使用 `environment.yml` 定义完整 conda 环境：
```bash
conda env create -f environment.yml -n scagent-dpm
conda activate scagent-dpm
```

### 1.2 Pip 依赖

`requirements.txt` 包含精确的 pip 依赖列表。对于关键依赖（numpy, scipy, pandas, scanpy, torch），建议在 `environment.yml` 中固定版本号。

### 1.3 Session Info

每次运行结束时，通过 `session-info` 包记录完整的 Python 包版本快照，保存到 `reproducibility_metadata.json`。

---

## 二、随机性控制

### 2.1 全局随机种子

- 配置文件中的 `seed` 参数（默认 42）
- 通过 `src/utils/reproducibility.py:set_seed()` 统一设置：
  - `random.seed(seed)`
  - `np.random.seed(seed)`
  - `torch.manual_seed(seed)`
  - `torch.cuda.manual_seed_all(seed)`
  - `torch.backends.cudnn.deterministic = True`
  - `torch.backends.cudnn.benchmark = False`
  - `os.environ['PYTHONHASHSEED'] = str(seed)`

### 2.2 种子记录

每次运行的 seed 值记录在：
- run_manifest.json 中的 config_snapshot
- reproducibility_metadata.json

---

## 三、配置管理

### 3.1 配置文件版本化

所有配置文件存放在 `configs/` 目录：
- `default.yaml`：默认全流程配置
- `server.yaml`：服务器批量实验配置
- `demo.yaml`：Demo 快速验证配置
- `experiment_*.yaml`：专项实验配置

### 3.2 配置快照

每次运行时，完整的配置字典写入：
- run_manifest.json 的 config_snapshot 字段
- reproducibility_metadata.json

禁止在代码中硬编码参数。所有参数必须通过配置文件传入。

---

## 四、数据管理

### 4.1 Raw Data 保护

- 原始数据（下载的 h5ad、fastq 等）存放在 `data/raw/`
- 原始数据永不覆盖、永不修改
- 所有处理后的数据存放在独立目录

### 4.2 Processed Data 版本化

处理后数据按运行时间戳组织：
```
results/<run_name>/
├── processed_adata.h5ad (可选)
├── ...
```

### 4.3 数据溯源

每次数据加载和处理记录在 run_manifest.json 中：
- 输入文件路径
- 数据摘要（细胞数、基因数、字段）
- 处理参数

---

## 五、Run Manifest

### 5.1 Manifest 结构

每次运行生成 `run_manifest.json`：
```json
{
  "run_name": "scAgent-DPM-demo_20240601_120000",
  "start_time": "2024-06-01T12:00:00",
  "end_time": "2024-06-01T12:05:30",
  "total_steps": 8,
  "steps": [
    {
      "step_index": 0,
      "module": "data_ingestion",
      "status": "success",
      "is_fallback": false,
      "timestamp": "...",
      "input_files": [],
      "output_files": ["data_summary.json"],
      "params": {...},
      "duration_seconds": 2.3
    }
  ],
  "config_snapshot": {...},
  "status_summary": {
    "success": 6, "failure": 0, "fallback": 2, "skipped": 0
  }
}
```

### 5.2 Execution Graph

`execution_graph.json` 记录模块执行依赖关系和有向无环图（DAG），包含每个节点的执行状态。

---

## 六、结果校验

### 6.1 文件校验

- 关键输出文件可选择性计算 SHA256 checksum
- checksum 记录在 manifest 或单独的 checksum 文件中

### 6.2 重复运行验证

对核心实验，使用相同 seed 和配置重复运行 3 次：
- 验证数值结果的一致性（允许浮点误差）
- 验证文件完整性（所有输出文件均生成）

### 6.3 跨平台验证

在本地（Windows）和服务器（Linux）上使用相同配置运行 demo：
- 验证流程可以执行完成
- 记录平台差异（如路径分隔符、GPU 可用性）

---

## 七、日志保留

### 7.1 日志组织

```
logs/
├── <run_name>.log          # 主日志
├── YYYYMMDD_HHMMSS_run.log # 按时间戳命名
└── server_runs/            # 服务器运行日志
```

### 7.2 日志级别

- DEBUG：写入文件（完整的函数调用和参数）
- INFO：写入控制台（关键步骤和结果）
- WARNING：非理想但可继续
- ERROR：失败，含 traceback

### 7.3 日志保留策略

- 成功运行日志：永久保留
- 失败运行日志：保留至问题解决
- Demo 和测试日志：可定期清理

---

## 八、模型权重管理

### 8.1 权重版本

- 记录模型权重路径和文件 hash
- 若使用预训练权重，记录下载来源和版本

### 8.2 权重缺失处理

- 配置文件支持指定模型路径
- 若路径为空或权重不存在 → fallback
- 在 manifest 中明确记录 fallback 原因

### 8.3 不同模型的 requirements

| 模型 | 权重来源 | 存储位置 |
|------|----------|----------|
| CellTypist | 内置自动下载 | ~/.celltypist/ |
| scGPT | 需手动下载或从 scGPT repo 获取 | config 指定 |
| scGPT-KDMT | 研究组项目产出 | config 指定 |
| Mamba-LSTM | 研究组项目产出 | config 指定 |

---

## 九、最终报告可复现性声明

每个最终报告包含以下可复现性信息：
- Python 版本
- 关键包版本
- 随机种子
- 配置文件路径
- 输入数据来源
- 运行时间戳
- 运行清单（manifest）路径
- Fallback 状态（若有）
