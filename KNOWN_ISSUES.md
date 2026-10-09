# Known issues

Issues are listed as they exist in the canonical source. Where a defect is a genuine bug rather than a
limitation, it is reported here **rather than silently patched**, so that the file hashes of this
release continue to match the code that produced the manuscript results.

---

## KI-1 — Dense matrix input trips a `memoryview` guard in the DEG path

**Severity:** medium (affects users with dense input only)
**Status:** open — reproduced in this release; **not** fixed in v1.1.0
**Affects:** `src/agent/executor.py`, `PipelineExecutor._prepare_deg_adata()`

### Description

```python
if hasattr(deg_adata.X, 'data'):
    _d = deg_adata.X.data          # dense ndarray -> numpy.memoryview
else:
    _d = deg_adata.X.toarray().flatten()
_is_log_norm = (_d.max() < 20) and (...)
```

For a **sparse** matrix, `X.data` is a NumPy `ndarray` and `.max()` works. For a **dense** NumPy array,
`ndarray.data` returns a **`memoryview`**, which has no `.max()` attribute, so the line raises:

```
AttributeError: 'memoryview' object has no attribute 'max'
```

The exception is caught by the module-level error handler, so the run does not abort — the
`perturbation` module is recorded as failed and the DEG/pathway outputs are not written.

The same construct appears in `src/data/preprocessing.py` but is safe there because it is wrapped in
`_np.asarray(...).flatten()` before use.

### Why this does not affect the manuscript results

All three canonical datasets are **sparse CSR** matrices
(`data_summary.json` records `scipy.sparse._csr.csr_matrix` for every run), so the dense branch was
never taken. The reported 2,280 / 170 / 2 DEG record counts are unaffected.

### Workaround for dense inputs

Convert to CSR before running, or keep the matrix sparse when writing the input:

```python
import scipy.sparse as sp
adata.X = sp.csr_matrix(adata.X)
```

### Suggested one-line fix (not applied here)

```python
_d = _np.asarray(deg_adata.X.data) if not hasattr(deg_adata.X, "toarray") else deg_adata.X.toarray()
```

or simply reuse the guarded form already present in `preprocessing.py`. Applying this changes the
SHA256 of `src/agent/executor.py` and would break the hash-anchoring of this release to the evaluated
code, so it is documented rather than applied. It is a candidate for a future release.

---

## KI-2 — The pipeline output manifest records no content hashes

**Severity:** low (documentation/disclosure issue)

`output_manifest.csv` lists emitted files with `path` and `size_bytes` only. A SHA256 helper
(`compute_file_checksum`) exists in `src/utils/reproducibility.py` but is **not called** by the
workflow, so the pipeline does not emit content checksums.

Content-hash verification was performed at a **separate audit layer** during the analysis project, not
by the workflow runtime. The two should not be conflated; see the README section
"Provenance and state tracking".

---

## KI-3 — No automatic resume

**Severity:** low (limitation, correctly described in the manuscript)

There is no resume subcommand. `main.py` exposes `check-env`, `init-project`, `run-demo`,
`run-pipeline`, `collect-results` and `generate-report` only. The workflow provides state persistence
and audit-supported recovery, not fault-tolerant resumption.

---

## KI-4 — Manifest integrity checking detects missing files, not modified files

**Severity:** low (scope limitation)

The fault-injection scenario R2 shows that a **deleted** manifest-listed file is detected. Detection is
by file existence, so a file that is modified in place but still present would **not** be detected. No
content-tamper detection is implemented.

---

## KI-5 — `config_snapshot` inside `run_manifest.json` is always `null`

**Severity:** low (cosmetic / documentation)

`PipelineState.save_manifest()` calls `to_manifest()` without passing the configuration, so the
`config_snapshot` field of `run_manifest.json` is `null`. The configuration **is** captured — as the
sibling file `config_snapshot.yaml` written by `PipelineExecutor._save_config_snapshot()`. Code and
documentation describing a populated `config_snapshot` field inside the run manifest are inaccurate.

---

## KI-6 — Annotation and dynamics modules require external checkpoints

**Severity:** low (by design)

scGPT / scGPT-KDMT annotation requires model checkpoints, and Mamba-LSTM dynamics requires a model
checkpoint plus time-course data. Neither is distributed here. Both modules are disabled
(`run_annotation: false`, `run_dynamics: false`) in all three canonical configurations.

---

## KI-7 — Pathway enrichment depends on the Enrichr web service

**Severity:** low (environmental)

Pathway enrichment calls gseapy Enrichr online by default. Results therefore depend on the availability
and version of the Enrichr libraries (KEGG 2021 Human, WikiPathway 2021 Human, GO Biological Process
2021). For offline or pinned-library reproduction, supply local GMT files and set
`perturbation.pathway.online: false`. Without local gene sets and with online access disabled, the
pathway status is recorded as unavailable.

---

## Reporting new issues

Please open an issue at <https://github.com/TheFinalDreamer/scAgent-DPM/issues> with a minimal
reproduction (the input's matrix state — dense or sparse — and the configuration used).
