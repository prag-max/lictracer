# 项目需求文档（PRD）

## 1. 项目概述

| 项目属性 | 内容                          |
| ---- | --------------------------- |
| 项目名称 | LicTracer（License + Tracer） |
| 项目定位 | 面向 AI 生成代码的许可证合规审计系统        |
| 核心价值 | 让 AI 生成的每一行代码，都有可追溯的许可证归属   |

## 2. 用户与使用场景

**目标用户**：

- 使用 AI 编程助手（如 Copilot、Cursor、ChatGPT）的开发者
- 开源项目维护者（需审核 AI 生成代码的合入）
- 企业的合规与法务部门

**核心使用场景**：

1. 开发者通过 **CLI 命令** 或 **Web 界面上传** 一段 AI 生成的代码文件
2. 系统自动分析代码中可能"混剪"自多个开源项目的片段
3. 系统输出一份 **合规审计报告**，包含：
   - 每个片段的来源项目与许可证
   - 兼容性分析结论（兼容/不兼容/需复核）
   - Copyleft 传染风险判断
   - 证据链（精确到行号）

## 3. 核心功能列表（按优先级）

| 优先级 | 功能模块      | 功能描述                                      |
| --- | --------- | ----------------------------------------- |
| P0  | 代码文件上传    | 支持通过 CLI 或 Web 上传单个代码文件（初期支持 `.py`）       |
| P0  | 代码预处理     | 使用 tree-sitter 进行 AST 解析与规范化（变量名统一化）      |
| P0  | 溯源检索      | 调用 NLCI 从知识库中召回相似候选代码                     |
| P0  | 证据精炼      | 调用 redup 对候选进行细粒度扫描，输出行级证据                |
| P0  | 多源聚合      | **自研**：将多个来源的证据按行号聚类，拆分不同来源片段             |
| P0  | 合规推理      | **自研**：基于 OSADL 矩阵进行多许可证推演与 Copyleft 传染判断 |
| P0  | 报告生成      | 输出结构化合规报告（JSON + 自然语言摘要）                  |
| P1  | Web 可视化界面 | 基于 Streamlit 提供上传与报告查看界面                  |
| P1  | 多种输出格式    | 支持 JSON、Markdown、HTML 格式报告导出              |

## 4. 非功能性需求

| 需求类型 | 具体要求                                       |
| ---- | ------------------------------------------ |
| 性能   | 不设定硬性时间约束；分析耗时随知识库规模与召回策略变化，以合规判定的正确性与可复现性为首要目标 |
| 确定性  | 合规推理结论 100% 可复现，零幻觉                        |
| 可审计性 | 每步推理均有证据链记录                                |
| 可扩展性 | 规则配置（许可证兼容性、Copyleft 策略）均通过 YAML 文件驱动，不硬编码 |
| 部署   | 支持 Docker Compose 一键部署                     |

## 5. 输入输出示例

**输入**：一个包含以下内容的 Python 文件 `sample.py`

```python
# 片段A：疑似来自 requests 库（MIT）
def send_request(url):
    return urllib.request.urlopen(url).read()

# 片段B：疑似来自某 GPL-3.0 项目
def calculate_interest(principal, rate, time):
    return principal * (1 + rate) ** time
```

**输出（摘要）**：

```json
{
  "summary": {
    "total_segments": 2,
    "risk_level": "HIGH",
    "conclusion": "INCOMPATIBLE"
  },
  "segments": [
    {
      "lines": "1-4",
      "source": "requests",
      "license": "MIT",
      "similarity": 0.92
    },
    {
      "lines": "6-8",
      "source": "finance-lib",
      "license": "GPL-3.0",
      "similarity": 0.88
    }
  ],
  "compliance_result": {
    "status": "INCOMPATIBLE",
    "reason": "GPL-3.0 片段与项目整体 MIT 许可证不兼容，且 GPL-3.0 具有 Copyleft 传染性"
  }
}
```

