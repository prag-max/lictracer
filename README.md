# LicTracer

面向 AI 生成代码的**许可证合规审计系统**（License + Tracer）。让 AI 生成的每一行代码，都有可追溯的许可证归属。

> **当前支持范围（v0.1）**：Python 单一语言检测；多语言扩展留待后续版本。评估体系已落地——受控合成基准（`evaluation/generate_benchmark.py`）+ 真实开源语料基准（`evaluation/real_corpus.py`），双基准指标见 `docs/评估基准报告.html`。

## 能力概览

```
原始代码(.py) → 预处理(tree-sitter 规范化) → 溯源召回(datasketch MinHash + Winnowing + AST 子树哈希)
             → 证据精炼(redup 行级) → 多源聚合(按行聚类拆分) → 合规推理(OSADL 矩阵 + Copyleft)
             → 报告生成(JSON / Markdown / HTML + 自然语言摘要)
```

- 预处理：标识符归一（`VAR_n` / `FUNC_n`）、去注释（tree-sitter 字节偏移，兼容中文；不可用时降级正则）
- 溯源：**多特征 MinHash 相似召回**——运算符感知分词 + Winnowing（MOSS 式指纹）+ AST 子树哈希（Merkle），
  MinHash(128, seed=1) 完全确定可复现；全库确定性 Jaccard 扫描（O(N×num_perm) 整数级比较，结果 100% 确定，无近似检索）
- 证据：`redup` 行级对比（阈值 0.5 可配），带调用缓存
- 合规：OSADL 兼容性矩阵（`osadl-matrix` pip 包，支持 OR/AND 复合许可证）+ YAML 驱动的 Copyleft 传染判断
- 结论：`COMPATIBLE` / `INCOMPATIBLE` / `NEEDS_REVIEW`，含推演步骤证据链与 `methodology` 方法学声明

## 依赖版本锁定表

| 包 | 版本 | 说明 |
| --- | --- | --- |
| tree-sitter | 0.26.0 | AST 解析 |
| tree-sitter-python | 0.25.0 | Python 语法包（锁定上界，避免 API 漂移） |
| datasketch | >=2.0.0 | MinHash Jaccard 估计（全库确定性扫描，Forest 已移除） |
| redup | 0.4.46 | 行级证据精排（精排 oracle） |
| osadl-matrix | 2024.5.22.10535 | 兼容性矩阵数据包（**2024-05 快照**，新许可证不会自动更新，须手动升版） |
| license-expression | 30.4.4 | SPDX 表达式解析/标准化 |
| pyyaml / python-dotenv / click | >= | 配置与入口 |

> 依赖的「事实来源」为 `pyproject.toml`（`pip install -e .` 时生效）；`requirements.txt` 与其严格同步，供复现安装使用。

## 快速开始

### 本地虚拟环境

```bash
# Windows（PowerShell）
python -m venv .venv
.venv\Scripts\python -m pip install -e .        # 安装 src 包（pyproject 驱动，含全部依赖）

# 跑测试
.venv\Scripts\python -m pytest tests/ -q

# CLI 分析内置示例（两种等价入口）
.venv\Scripts\lictracer analyze sample.py --format json
.venv\Scripts\python -m src.cli.main analyze sample.py --format json
```

> 安装后 `import src.*` 由已安装包解析，代码中不再有 `sys.path` hack。

### 部署形态

- **桌面端（唯一用户交付形态）**：PySide6 单窗口应用（`src/ui/`），本地离线、代码不出本机。
  开发态运行 `.venv\Scripts\lictracer-gui`（或 `python -m src.ui.main`）；
  发布构建 `powershell -File packaging\build_exe.ps1` → 免安装 onedir 产物 `dist/LicTracer/`
  （内置默认知识库随包分发，高级选项可覆盖自定义 KB），发布前按
  `docs/桌面端发布自检清单.md` 在干净机器逐项核验。
- **CLI（无界面入口，保留）**：批量检测、评测复现、脚本集成，不依赖 GUI 与网络。
- **服务部署已退役**：原 FastAPI / Streamlit / Docker 部署形态已移除（见 `docs/发布前验证报告.html` 退役说明），相关 `LICT_API_TOKEN` / `LICT_MAX_UPLOAD_BYTES` 等环境变量不再生效。

## 报告与输出

`analyze_file` 产出结构化 JSON 报告，含：

- `compliance_result`：最终结论（`COMPATIBLE` / `INCOMPATIBLE` / `NEEDS_REVIEW`）+ 风险等级 + 推演证据链
- `segments`：逐片段命中（来源项目、许可证、相似度、合规判定）
- `evidence`：redup 行级证据
- `methodology`：方法学声明（`tree_sitter` 状态、`retriever_mode`、`kb_files`），降级可见、可复现

```bash
.venv\Scripts\lictracer analyze sample.py --format json
```

## 配置

- `config/settings.yaml`：项目整体许可证（默认 MIT）、知识库路径、`top_k`、链接方式等
- `config/license_rules.yaml`：Copyleft 传染策略（GPL/AGPL/LGPL 的 static/dynamic 规则）
- 环境变量：`LICT_WINNOW_WINDOW`、`LICT_REDUP_MIN_SIM` / `LICT_REDUP_FUNCTIONS_ONLY`、
  `LICT_LLM_TIMEOUT` / `LICT_LLM_MASK_SOURCE` / `LICT_ENABLE_LLM`
  （注：原 API 专用的 `LICT_API_TOKEN` / `LICT_MAX_UPLOAD_BYTES` 已随服务部署退役）
- `.env`（复制自 `.env.example`）：可选的大模型 API Key（仅作摘要“翻译官”，不参与判断，默认关闭）

## 结论判据

| 情况 | 结论 | 风险 |
| --- | --- | --- |
| 存在片段与项目许可证不兼容（矩阵 NO），且为 GPL 系列 | INCOMPATIBLE（含 Copyleft 传染标注） | HIGH |
| 存在片段不兼容（矩阵 NO），非 GPL 系列 | INCOMPATIBLE | HIGH |
| 存在兼容性未知（矩阵 UNKNOWN） | NEEDS_REVIEW | MEDIUM |
| 全部兼容 | COMPATIBLE | LOW |

示例：项目整体 MIT + 片段 GPL-3.0 → **INCOMPATIBLE**。

## 已知局限（诚实声明）

- 仅支持 Python；`similarity` 为 MinHash **估计值**（±7.4%@128 排列），仅作候选排序与报告展示，**不参与克隆裁决**；
- 溯源召回为**全库确定性 Jaccard 扫描**（非近似检索，召回确定性 100%）；本系统 KB 为提取实体集（O(百) 文件），全库扫描实测毫秒级，远低于 LSH Forest 亚线性代价生效的 2000+ 文件阈值，故 Forest 已于 2026-08-23 移除；锚点召回索引按进程内构建；
- 端到端克隆判定经**确定性等价验证器**（`src/provenance/exact_verifier.py`）完成，**决策路径无浮点阈值**：
  - L1 规范型精确相等（逐字 / 重命名 T1/T2）；
  - L2 结构语句序列包含（保序子序列，容忍噪声语句插入的 near-miss T3），覆盖**三类结构层级**：L2a 函数体（仅模块级函数）、L2b 类体（类属性赋值 + 方法签名——v4.2 起签名含**方法名**，消除无参方法哈希碰撞，`MIN_L2_STMTS`=3 防空壳类）、L2c 模块级（纯模块片段，≥ `MIN_MODULE_STMTS`=4 条防通用 import 误报）；
  - L3 锚点行游程（≥ `min_anchor_lines` 行连续规范化行命中，召回闸门，覆盖语句删除 / 重排残留）；
  - 旧结构兜底 `e2e_clone_threshold=0.30` 已移除；redup 行级证据改为**计数式闸门**（≥ `LICT_REDUP_MIN_LINES`=3 行命中），仅作补充性证据；
- **评估体系（双基准 + 主证据融合）**：受控合成基准（57 查询，7 类改写：exact/renamed/transformed/deleted/reordered/class_attr/cross_file）+ 真实开源语料基准（484 查询，KB 为 **11 个真实开源包** tree-sitter 提取的 **111 个真实函数/类实体**，含 beancount(GPL-2.0) / mozinfo(MPL-2.0) / python-telegram-bot(LGPL-3.0) 等「正确拒绝」不兼容正例，源码归档 `data/raw_sources/`），粗筛召回 / 端到端召回 / 确定性证据率 / **归属准确率** / 合规准确率均 1.000，负样本零假阳性（真实语料负样本经确定性验证器零匹配过滤）。**主证据融合（次优证据融合）**：聚合层异源证据不合并（每段单一来源）、`rank_primary` 按 (similarity, verification_level) 在已验证段中取主证据源（布尔判定门控 × 相似度排序）、`attribution_of` 对 (level, sim) 完全并列的异源段显式标记 `attribution_ambiguous`。复现：`python -m evaluation.generate_benchmark && python -m evaluation.run_eval`、`python -m evaluation.real_corpus && python -m evaluation.run_eval --bench benchmark_real`；
- **残差（诚实边界）**：语义等价重写（T4）与重度交错改写（语句 A,B,C → A,X,B,Y,C 且行级游程 < 3）不在确定性保证内——不静默判定，由报告经 `verification_level` 显式暴露证据强度；真实跨项目结构近邻的归属歧义已由主证据融合收窄（归属准确率实测 1.0），仅 (level, sim) 完全并列时置 `attribution_ambiguous`；numpy / pandas 复合 SPDX 含 OSADL 未收录成分时保守判 `NEEDS_REVIEW`（基准以其主许可证为代表）；
- **主证据驱动的合规聚合（v4 / v4.1 / v4.2）**：合规结论由**强证据段（L1/L2）∪ 主证据段**驱动（`src/pipeline.py::select_conclusion_segments`），非主证据的弱证据段（L3/4）仅作报告展示（段带 `drives_conclusion`、报告含 `conclusion_segment_ids`）——弱伪匹配携带的高危害许可证不再污染结论。混合许可证基准（`evaluation/benchmark_mixed.py`：真实 6 包 + **真实 GPL-2.0/MPL-2.0/LGPL-3.0 开源包干扰** beancount / mozinfo / python-telegram-bot，58 个与目标自然 L3 弱匹配的真实函数）实测：**旧聚合（全段参与）149 条合规误报 → 新聚合 0 条（100% 消除），归属准确率 1.0**；
- OSADL 矩阵为 2024-05 快照；`licenses.json` 缺失映射的项目按 UNKNOWN 处理（扫描时告警）。
