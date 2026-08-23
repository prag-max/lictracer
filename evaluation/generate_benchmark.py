# -*- coding: utf-8 -*-
"""生成 LicTracer 受控评估基准（controlled benchmark）。

产出：
- data/benchmark/kb/            基准知识库（projects/<project>/<file>.py + licenses.json）
- data/benchmark/queries/       查询集（精确克隆 / 变量改名 / 等价改写 / 无关负样本）
- data/benchmark/ground_truth.json

说明（诚实声明）：
本基准为**受控合成基准**——KB 函数为基于真实开源库标志性实现的
手写片段（标注其真实 SPDX 许可证），并非整库爬取。目的是在
可控 ground truth 下量化检索/合规管线的 Recall / Precision / F1 与
合规准确率，作为评估体系（P0-1）的第一步。真实项目整库评测为
future work（见 docs/评估基准报告.html）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmark"
KB_DIR = BENCH / "kb"
PROJ_DIR = KB_DIR / "projects"
QUERY_DIR = BENCH / "queries"

# ---------------------------------------------------------------------------
# KB 函数：project -> (SPDX 许可证, 真实风格源码)
# 许可证均为对应上游项目的真实许可证。
# ---------------------------------------------------------------------------
KB_FUNCS = {
    "requests": ("MIT", (
        "# 源自 requests 项目（MIT License）：简化的 HTTP GET 封装\n"
        "import urllib.request\n"
        "\n"
        "def http_get(url, timeout=10):\n"
        "    req = urllib.request.Request(url)\n"
        "    with urllib.request.urlopen(req, timeout=timeout) as resp:\n"
        "        return resp.read().decode(\"utf-8\")\n"
    )),
    "flask": ("BSD-3-Clause", (
        "# 源自 Flask 项目（BSD-3-Clause）：最小应用工厂\n"
        "from flask import Flask\n"
        "\n"
        "def create_app(name=\"app\"):\n"
        "    app = Flask(name)\n"
        "    @app.route(\"/\")\n"
        "    def index():\n"
        "        return \"hello\"\n"
        "    return app\n"
    )),
    "numpy": ("BSD-3-Clause", (
        "# 源自 NumPy 项目（BSD-3-Clause）：多项式最小二乘拟合（简化）\n"
        "import numpy as np\n"
        "\n"
        "def polyfit(x, y, deg):\n"
        "    X = np.vander(x, deg + 1)\n"
        "    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)\n"
        "    return coeffs\n"
    )),
    "pandas": ("BSD-3-Clause", (
        "# 源自 pandas 项目（BSD-3-Clause）：分组均值聚合\n"
        "import pandas as pd\n"
        "\n"
        "def group_mean(frame, key, value):\n"
        "    return frame.groupby(key)[value].mean()\n"
    )),
    "django": ("BSD-3-Clause", (
        "# 源自 Django 项目（BSD-3-Clause）：视图缓存装饰器\n"
        "from functools import wraps\n"
        "\n"
        "def cache_page(seconds=60):\n"
        "    def decorator(view):\n"
        "        @wraps(view)\n"
        "        def wrapper(*args, **kwargs):\n"
        "            return view(*args, **kwargs)\n"
        "        return wrapper\n"
        "    return decorator\n"
    )),
    "click": ("BSD-3-Clause", (
        "# 源自 Click 项目（BSD-3-Clause）：命令行命令定义\n"
        "import click\n"
        "\n"
        "@click.command()\n"
        "@click.option(\"--name\", default=\"world\")\n"
        "def hello(name):\n"
        "    click.echo(f\"Hello {name}\")\n"
    )),
    "pyyaml": ("MIT", (
        "# 源自 PyYAML 项目（MIT License）：安全加载配置文件\n"
        "import yaml\n"
        "\n"
        "def load_config(path):\n"
        "    with open(path, \"r\", encoding=\"utf-8\") as f:\n"
        "        return yaml.safe_load(f)\n"
    )),
    "scipy": ("BSD-3-Clause", (
        "# 源自 SciPy 项目（BSD-3-Clause）：牛顿迭代求根\n"
        "def newton(f, df, x0, tol=1e-8, maxiter=100):\n"
        "    x = x0\n"
        "    for _ in range(maxiter):\n"
        "        x = x - f(x) / df(x)\n"
        "        if abs(f(x)) < tol:\n"
        "            break\n"
        "    return x\n"
    )),
    "celery": ("BSD-3-Clause", (
        "# 源自 Celery 项目（BSD-3-Clause）：任务定义\n"
        "from celery import Celery\n"
        "\n"
        "app = Celery(\"tasks\", broker=\"redis://localhost\")\n"
        "\n"
        "@app.task\n"
        "def add(a, b):\n"
        "    return a + b\n"
    )),
    "arrow": ("Apache-2.0", (
        "# 源自 Arrow 项目（Apache-2.0）：指定时区的当前时间\n"
        "import arrow\n"
        "\n"
        "def now_in_tz(tz=\"UTC\"):\n"
        "    return arrow.now(tz)\n"
    )),
    "gpl-crypto": ("GPL-3.0", (
        "# 源自某 GPL-3.0 加密库：SHA-256 十六进制摘要\n"
        "import hashlib\n"
        "\n"
        "def sha256_hex(data):\n"
        "    if isinstance(data, str):\n"
        "        data = data.encode(\"utf-8\")\n"
        "    return hashlib.sha256(data).hexdigest()\n"
    )),
    "mpl-utils": ("MPL-2.0", (
        "# 源自某 MPL-2.0 工具库：数值钳制\n"
        "def clamp(value, low, high):\n"
        "    return max(low, min(value, high))\n"
    )),
    "lgpl-image": ("LGPL-3.0", (
        "# 源自某 LGPL-3.0 图像处理库：最近邻缩放（简化）\n"
        "def resize_nearest(pixels, src_w, src_h, dst_w, dst_h):\n"
        "    out = []\n"
        "    for j in range(dst_h):\n"
        "        for i in range(dst_w):\n"
        "            sx = int(i * src_w / dst_w)\n"
        "            sy = int(j * src_h / dst_h)\n"
        "            out.append(pixels[sy * src_w + sx])\n"
        "    return out\n"
    )),
}

# 长函数实体（函数体 ≥5 行）：专用于语句删除 / 重排改写类型（deleted / reordered）
KB_LONG_FUNCS = {
    "tokenizer": ("MIT", (
        "# 源自某分词库（MIT）：空白 + 标点切分（长函数，>5 行体）\n"
        "import re\n"
        "\n"
        "def tokenize(text):\n"
        "    tokens = []\n"
        "    for line in text.splitlines():\n"
        "        line = line.strip()\n"
        "        if not line:\n"
        "            continue\n"
        "        for piece in re.split(r\"\\W+\", line):\n"
        "            if piece:\n"
        "                tokens.append(piece.lower())\n"
        "    return tokens\n"
    )),
}

# 类实体（含类属性 + 方法）：专用于类属性克隆类型（class_attr）
KB_CLASSES = {
    "config-class": ("MIT", (
        "# 源自某配置库（MIT）：应用配置类（类属性 + 方法）\n"
        "class AppConfig:\n"
        "    DEBUG = False\n"
        "    SECRET_KEY = \"dev-secret\"\n"
        "    MAX_RETRIES = 3\n"
        "    TIMEOUT = 30\n"
        "    def get(self, key, default=None):\n"
        "        return getattr(self, key, default)\n"
        "    def set(self, key, value):\n"
        "        setattr(self, key, value)\n"
    )),
}

# 与任何 KB 无关的业务代码（负样本）
NEGATIVES = {
    "quicksort": (
        "def quicksort(arr):\n"
        "    if len(arr) <= 1:\n"
        "        return arr\n"
        "    pivot = arr[len(arr) // 2]\n"
        "    left = [x for x in arr if x < pivot]\n"
        "    mid = [x for x in arr if x == pivot]\n"
        "    right = [x for x in arr if x > pivot]\n"
        "    return quicksort(left) + mid + quicksort(right)\n"
    ),
    "fibonacci": (
        "def fib(n):\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    ),
    "file_copy": (
        "def copy_file(src, dst):\n"
        "    with open(src, \"rb\") as f:\n"
        "        data = f.read()\n"
        "    with open(dst, \"wb\") as f:\n"
        "        f.write(data)\n"
    ),
    "calculator": (
        "def calc(a, b, op):\n"
        "    if op == \"+\":\n"
        "        return a + b\n"
        "    if op == \"-\":\n"
        "        return a - b\n"
        "    if op == \"*\":\n"
        "        return a * b\n"
        "    return a / b\n"
    ),
    "binary_search": (
        "def binary_search(arr, target):\n"
        "    lo, hi = 0, len(arr) - 1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        if arr[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return -1\n"
    ),
    "word_count": (
        "def count_words(text):\n"
        "    words = text.split()\n"
        "    result = {}\n"
        "    for w in words:\n"
        "        result[w] = result.get(w, 0) + 1\n"
        "    return result\n"
    ),
    "matrix_multiply": (
        "def matmul(a, b):\n"
        "    n = len(a)\n"
        "    c = [[0] * n for _ in range(n)]\n"
        "    for i in range(n):\n"
        "        for j in range(n):\n"
        "            for k in range(n):\n"
        "                c[i][j] += a[i][k] * b[k][j]\n"
        "    return c\n"
    ),
    "linked_list": (
        "class Node:\n"
        "    def __init__(self, val):\n"
        "        self.val = val\n"
        "        self.next = None\n"
        "\n"
        "def to_list(head):\n"
        "    out = []\n"
        "    while head:\n"
        "        out.append(head.val)\n"
        "        head = head.next\n"
        "    return out\n"
    ),
}

# 参考项目许可证（与 settings.yaml 一致）= MIT
PROJECT_LICENSE = "MIT"

# 命中源许可证 vs 参考项目(MIT) 的预期合规结论。
# 基于 OSADL 兼容性矩阵实测（见 evaluation/run_eval.py 的 is_compatible 校验）：
#   MIT/BSD/Apache vs MIT = YES;  MPL-2.0/LGPL-3.0/GPL-3.0 vs MIT = NO
# 注：MPL-2.0 / LGPL-3.0 与 MIT 在 OSADL 2024-05 快照中为 NO（不兼容）。
LICENSE_EXPECTED_COMPAT = {
    "MIT": "COMPATIBLE",
    "BSD-3-Clause": "COMPATIBLE",
    "Apache-2.0": "COMPATIBLE",
    "MPL-2.0": "INCOMPATIBLE",
    "LGPL-3.0": "INCOMPATIBLE",
    "GPL-3.0": "INCOMPATIBLE",
}


def _renamed(code: str, idx: int) -> str:
    """变量/参数改名变体（测试 G 特征抗重命名 T2）。

    仅改写 def 内的参数名与函数名，不触碰 import / 装饰器 / 库名，
    避免破坏真实依赖。函数体内对参数的引用同步替换。
    """
    lines = code.splitlines()
    out: list[str] = []
    param_map = None
    for ln in lines:
        m = re.match(r"\s*def\s+(\w+)\s*\(([^)]*)\)", ln)
        if m:
            params = [
                p.split("=")[0].split(":")[0].strip()
                for p in m.group(2).split(",")
                if p.strip()
            ]
            param_map = {p: f"arg{j}" for j, p in enumerate(params)}
            ln = re.sub(r"(def\s+)\w+", rf"\g<1>func{idx}", ln)
            for p in params:
                ln = re.sub(r"\b" + re.escape(p) + r"\b", param_map[p], ln)
            out.append(ln)
            continue
        if param_map:
            for p in param_map:
                ln = re.sub(r"\b" + re.escape(p) + r"\b", param_map[p], ln)
        out.append(ln)
    return "\n".join(out)


def _transformed(code: str, idx: int) -> str:
    """等价改写变体（测试 L2 结构语句序列包含对 near-miss 的鲁棒性 T3）。

    在**首个** def 的函数体首行**之前**插入一条无关赋值语句（合法语法、不破坏
    控制流），并在文件顶部加注释；嵌套 def（装饰器内函数等）不再重复插入，
    保证产物始终是合法 Python。插入语句的缩进取自被插行（函数体首行）的
    实际缩进——模块级函数为 4 空格（与旧行为一致），类方法为 8 空格，
    使类实体的 transformed 变体也是合法 Python。噪声行可被任意插入位置的
    保序子序列匹配（L2）容忍，与真实 near-miss 改写一致。
    """
    lines = code.splitlines()
    out = ["# 自动生成的重构变体（重排与微调，near-miss）"]
    pending = False
    done = False
    for ln in lines:
        if not done:
            if ln.strip().startswith("def ") and not pending:
                out.append(ln)
                pending = True
                continue
            if pending:
                if ln[:1] in (" ", "\t"):
                    if ln.strip():
                        indent = ln[: len(ln) - len(ln.lstrip())]
                        out.append(f"{indent}_tmp_{idx} = 1  # near-miss 微调")
                        done = True
                    pending = False
                elif ln.strip():
                    pending = False  # 首个 def 后无缩进体（空体/注释），放弃插入
        out.append(ln)
    return "\n".join(out)


def _stmt_deleted(code: str, idx: int) -> str:
    """语句删除变体（测试 L3 锚点召回对「删中间语句」的鲁棒性；T4-delete）。

    删除首个函数体的第 2 条语句（保留末尾 ≥3 条连续 → 与 KB 共享末尾 3 连续
    规范行 → L3 锚点命中，确定性布尔）。仅当函数体 ≥5 行时有效；否则返回原码
    （调用方应跳过过短函数）。删除用 tree-sitter 语句行号精确操作。
    """
    from src.preprocessor.ast_normalizer import ast_statement_sequences

    _, funcs, _, ok = ast_statement_sequences(code)
    if not ok or not funcs:
        return code
    stmts = funcs[0]["stmts"]
    if len(stmts) < 5:
        return code
    sl, el = stmts[1][1], stmts[1][2]  # 第 2 条语句行范围（1-based）
    lines = code.splitlines()
    new = lines[: sl - 1] + lines[el:]
    return "\n".join(new)


def _stmt_reordered(code: str, idx: int) -> str:
    """语句重排变体（测试 L3 锚点召回对「交换中间相邻语句」的鲁棒性；T4-reorder）。

    交换首个函数体第 4、5 条语句（保留前 3 条连续不变 → 与 KB 共享前 3 连续规范
    行 → L3 锚点命中，确定性布尔）。仅当函数体 ≥5 行时有效；否则返回原码。
    """
    from src.preprocessor.ast_normalizer import ast_statement_sequences

    _, funcs, _, ok = ast_statement_sequences(code)
    if not ok or not funcs:
        return code
    stmts = funcs[0]["stmts"]
    if len(stmts) < 5:
        return code
    a, b = stmts[3], stmts[4]  # 第 4、5 条语句
    lines = code.splitlines()
    block_a = lines[a[1] - 1 : a[2]]
    block_b = lines[b[1] - 1 : b[2]]
    new = lines[: a[1] - 1] + block_b + block_a + lines[b[2] :]
    return "\n".join(new)


def _class_attr_clone(code: str, idx: int) -> str:
    """类属性克隆变体（测试 L2b 类体结构包含；T5）。

    复制 KB 类，改名类名并插入一条无关属性 → 规范型不等（L1 不命中），但类体
    结构序列（原属性 + 方法签名）仍保序包含 → L2b 命中（level 2）。
    """
    lines = code.splitlines()
    out = []
    renamed = False
    for ln in lines:
        if not renamed and ln.strip().startswith("class "):
            ln = re.sub(r"class\s+\w+", f"class ConfigClone{idx}", ln)
            renamed = True
            out.append(ln)
            out.append(f"    _clone_marker_{idx} = {idx}")  # 类体内插入无关属性
            continue
        out.append(ln)
    return "\n".join(out)


def _cross_file(codes: "list[str]", idx: int) -> str:
    """跨文件克隆变体（测试多源召回；T7）：拼接多个 KB 实体真实源码到一个文件。

    ground truth 的 ``expected_project`` 为来源项目列表（多源）。
    """
    return "\n\n".join(codes)


def main() -> None:
    # 重建目录（直接覆盖写，不删除既有文件以避免批量删除触发安全门）
    for d in (PROJ_DIR, QUERY_DIR):
        d.mkdir(parents=True, exist_ok=True)
    (KB_DIR / ".index").mkdir(parents=True, exist_ok=True)

    # 1) 写 KB（函数型 + 长函数 + 类）
    licenses = {}
    all_func_kbs = {**KB_FUNCS, **KB_LONG_FUNCS}
    for project, (lic, code) in {**all_func_kbs, **KB_CLASSES}.items():
        (PROJ_DIR / project).mkdir(parents=True, exist_ok=True)
        fname = f"{project.replace('-', '_')}.py"
        (PROJ_DIR / project / fname).write_text(code, encoding="utf-8")
        licenses[project] = lic
    (KB_DIR / "licenses.json").write_text(
        json.dumps(licenses, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 2) 生成 queries + ground truth
    ground_truth: list[dict] = []
    qid = 0

    # 2a) 函数型（KB_FUNCS + KB_LONG_FUNCS）：exact / renamed / transformed
    #     + 长函数附加 deleted / reordered
    for idx, (project, (lic, code)) in enumerate(all_func_kbs.items(), start=1):
        expected_compat = LICENSE_EXPECTED_COMPAT[lic]
        variants = {
            "exact": code,
            "renamed": _renamed(code, idx),
            "transformed": _transformed(code, idx),
        }
        if project in KB_LONG_FUNCS:
            variants["deleted"] = _stmt_deleted(code, idx)
            variants["reordered"] = _stmt_reordered(code, idx)
        for kind, qcode in variants.items():
            qid += 1
            qname = f"q{qid:03d}_{kind}_{project}.py"
            (QUERY_DIR / qname).write_text(qcode, encoding="utf-8")
            ground_truth.append(
                {
                    "id": qname,
                    "kind": kind,
                    "expected_project": project,
                    "expected_license": lic,
                    "expected_compat": expected_compat,
                }
            )

    # 2b) 类型（KB_CLASSES）：exact / renamed / transformed / class_attr
    for idx, (project, (lic, code)) in enumerate(KB_CLASSES.items(), start=100):
        expected_compat = LICENSE_EXPECTED_COMPAT[lic]
        variants = {
            "exact": code,
            "renamed": _renamed(code, idx),
            "transformed": _transformed(code, idx),
            "class_attr": _class_attr_clone(code, idx),
        }
        for kind, qcode in variants.items():
            qid += 1
            qname = f"q{qid:03d}_{kind}_{project}.py"
            (QUERY_DIR / qname).write_text(qcode, encoding="utf-8")
            ground_truth.append(
                {
                    "id": qname,
                    "kind": kind,
                    "expected_project": project,
                    "expected_license": lic,
                    "expected_compat": expected_compat,
                }
            )

    # 2c) 跨文件克隆（多源）：拼接多个函数型 KB 实体真实源码
    cf_projects = [p for p in ("requests", "numpy", "flask") if p in all_func_kbs]
    if len(cf_projects) >= 2:
        qid += 1
        qcode = _cross_file([all_func_kbs[p][1] for p in cf_projects], 1)
        qname = f"q{qid:03d}_cross_file_multi.py"
        (QUERY_DIR / qname).write_text(qcode, encoding="utf-8")
        # 多源兼容：所有来源均为 MIT/BSD-3-Clause vs 参考项目 MIT = COMPATIBLE
        ground_truth.append(
            {
                "id": qname,
                "kind": "cross_file",
                "expected_project": cf_projects,  # 列表 = 多源
                "expected_license": None,
                "expected_compat": "COMPATIBLE",
            }
        )

    # 2d) 负样本（与任何 KB 无关的业务代码）
    for name, code in NEGATIVES.items():
        qid += 1
        qname = f"q{qid:03d}_negative_{name}.py"
        (QUERY_DIR / qname).write_text(code, encoding="utf-8")
        ground_truth.append(
            {
                "id": qname,
                "kind": "negative",
                "expected_project": None,
                "expected_license": None,
                "expected_compat": "COMPATIBLE",
            }
        )

    (BENCH / "ground_truth.json").write_text(
        json.dumps(
            {
                "project_license": PROJECT_LICENSE,
                "kb_path": str(KB_DIR),
                "queries": ground_truth,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    n_pos = sum(1 for g in ground_truth if g["kind"] != "negative")
    n_neg = sum(1 for g in ground_truth if g["kind"] == "negative")
    print(f"KB projects: {len(licenses)}  (licenses: {sorted(set(licenses.values()))})")
    print(f"queries: {len(ground_truth)}  (positive={n_pos}, negative={n_neg})")
    print(f"written -> {BENCH}")


if __name__ == "__main__":
    main()
