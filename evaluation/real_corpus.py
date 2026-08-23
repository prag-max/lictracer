# -*- coding: utf-8 -*-
"""生成 LicTracer 真实开源语料基准（real open-source corpus benchmark）。

与受控合成基准（data/benchmark）互补：本基准从**本机已安装的真实开源包**
（click / datasketch / license_expression / charset_normalizer / numpy / pandas，
其源码与 SPDX 许可证均为真实可查）用 tree-sitter 提取中等规模的函数 / 类实体，
作为知识库（KB）真实片段；再对每段施加与合成基准一致的改写变体
（exact / renamed / transformed / deleted / reordered / class_attr），
在真实代码分布下量化检索 / 确定性 / 合规指标。

设计取舍（诚实声明）：
- KB 实体为**真实开源源码片段**（含装饰器、类型标注、文档字符串），非手写；
  许可证取自包元数据真实 SPDX；numpy / pandas 元数据为复合 SPDX
  （BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0），其中的 0BSD / CC0-1.0
  等成分 OSADL 矩阵未收录 → 整体判 NEEDS_REVIEW，会污染保守合规结论；故本基准
  以各包**主许可证 BSD-3-Clause** 作为代表 SPDX（与项目 MIT 参考许可证 COMPATIBLE）
  参与确定性合规基准，复合许可证解析本身由 matrix_loader 单独覆盖（见未来工作）；
- 实体筛选：函数体语句数 ∈ [5,40] 且函数名非 dunder / 非常见名（降低跨包
  同名近邻导致的粗筛混淆）；类体成员 ≥2（含类属性或方法）；文件大小 0.8–35KB
  跳过巨型 / 测试文件，保证可解析与中等规模；
- 文件名按包内小写去重（Windows NTFS 大小写不敏感，``MinHash.py`` 与
  ``minhash.py`` 会冲突覆盖）；负样本经**确定性验证器全证据零匹配过滤**——
  对候选逐一比对全部 KB 实体，L1 规范型 / L2 结构包含 / L3 锚点游程任一命中
  即剔除（覆盖单语句 L2 过度匹配等全部判定路径），确保负样本在决策路径上与
  任何 KB 实体都不构成克隆；
- 改写变体复用 evaluation.generate_benchmark 的生成器与负样本，保证两套基准
  方法论一致、可横向对比；
- 真实语料用于检验确定性等价验证器（L1/L2/L3 布尔判定）在真实代码分布下的
  泛化性：端到端召回 / 确定性证据率 / 合规准确率为验证器保证的稳健属性，
  粗筛召回为启发式排序。真实跨项目代码可能存在结构近邻（两份真实代码结构相似），
  此时验证器必能检出克隆但来源归属可能指向结构相似的他包——此归属歧义为纯结构
  匹配的已知残差（已在 exact_verifier 文档明示），合规结论因本基准所选许可证
  均兼容而不受影响，结果如实报告。

运行：``python -m evaluation.real_corpus``
"""
from __future__ import annotations

import importlib.metadata as _md
import importlib.util as _util
import json
import logging
import re
from pathlib import Path

logging.disable(logging.CRITICAL)

# tree-sitter 解析（与 ast_normalizer 同加载方式）
try:
    import tree_sitter as _ts  # type: ignore
    import tree_sitter_python as _tspy  # type: ignore

    _TSL = _ts.Language(_tspy.language())
    _TS_OK = True
except Exception:  # pragma: no cover - 退化分支
    _TSL = None
    _TS_OK = False
    logging.warning("tree-sitter 不可用，真实语料提取无法进行", exc_info=True)

# 合规兼容性复用流水线的同一 OSADL 矩阵查询
from src.compliance.license_normalizer import normalize as _lic_norm  # noqa: E402
from src.compliance.matrix_loader import is_compatible as _is_compat  # noqa: E402
from src.provenance.exact_verifier import verify as _verify  # noqa: E402

# 复用合成基准的改写生成器与负样本（保证方法论一致）
from evaluation.generate_benchmark import (  # noqa: E402
    NEGATIVES,
    _class_attr_clone,
    _renamed,
    _stmt_deleted,
    _stmt_reordered,
    _transformed,
)

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmark_real"
KB_DIR = BENCH / "kb"
PROJ_DIR = KB_DIR / "projects"
QUERY_DIR = BENCH / "queries"

# 目标真实包：本机已安装（click/datasketch/.../scipy）或 data/raw_sources/ 归档
# （beancount/telegram/mozinfo，PyPI wheel 解压，许可证从 METADATA 验证）。许可证
# 从元数据真实检测；新增 GPL-2.0 / LGPL-3.0 / MPL-2.0 不兼容包作为「正确拒绝」
# 的正例方向（查询 expected_compat=INCOMPATIBLE）。
TARGET_PACKAGES = [
    "click",
    "datasketch",
    "license_expression",
    "charset_normalizer",
    "numpy",
    "pandas",
    "altair",
    "scipy",
    "beancount",
    "telegram",
    "mozinfo",
]

# 复合 SPDX 包以主许可证作为代表参与确定性合规基准（说明见模块 docstring）
REPRESENTATIVE_LICENSE = {
    "numpy": "BSD-3-Clause",
    "pandas": "BSD-3-Clause",
}

# data/raw_sources/ 归档包的真实 SPDX（wheel METADATA 验证；未安装故无 importlib 元数据）
RAW_PACKAGE_LICENSES = {
    "beancount": "GPL-2.0",
    "telegram": "LGPL-3.0",
    "mozinfo": "MPL-2.0",
}

# 每个包抽取的实体预算（按函数体/类体规模降序取前 N）
FUNCS_PER_PKG = 8
CLASSES_PER_PKG = 3

# 文件大小窗口（字节）：跳过过小（无意义）与过大（巨型文件、解析慢）的源
_MIN_FILE = 800
_MAX_FILE = 35_000

# 常见/非特异函数名：排除后降低跨包同名近邻造成的粗筛混淆
COMMON_NAMES = {
    "__init__", "__repr__", "__str__", "__eq__", "__hash__", "__len__",
    "__getitem__", "__setitem__", "__call__", "__enter__", "__exit__",
    "__iter__", "__next__", "__contains__", "__del__", "__new__",
    "run", "main", "get", "set", "copy", "clone", "build", "create",
    "init", "close", "open", "read", "write", "start", "stop", "update",
    "add", "remove", "find", "parse", "load", "save", "dump", "make",
    "new", "apply", "reset", "clear", "show", "setup", "check", "to_dict",
    "from_dict", "validate", "format", "convert", "process", "handle",
}

# OSI 分类器名 → SPDX（元数据 License-Expression 缺失时兜底）
_CLASSIFIER_TO_SPDX = {
    "BSD License": "BSD-3-Clause",
    "MIT License": "MIT",
    "Apache Software License": "Apache-2.0",
    "GNU General Public License v2 (GPLv2)": "GPL-2.0",
    "GNU General Public License v3 (GPLv3)": "GPL-3.0",
    "GNU Lesser General Public License v3 (LGPLv3)": "LGPL-3.0",
    "GNU Lesser General Public License v2 (LGPLv2)": "LGPL-2.1",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Python Software Foundation License": "Python-2.0",
}

# 参考项目许可证（与合成基准、流水线默认一致）= MIT
PROJECT_LICENSE = "MIT"

_COMPAT_MAP = {"YES": "COMPATIBLE", "NO": "INCOMPATIBLE", "UNKNOWN": "NEEDS_REVIEW"}

# 负样本补充池（真实风格算法；经锚点非碰撞过滤后取前 8，确保不与任何 KB 实体
# 共享 ≥3 连续规范行，避免通用实现被误判为克隆）
NEG_POOL = {
    **NEGATIVES,
    "bubble_sort": (
        "def bubble_sort(arr):\n"
        "    n = len(arr)\n"
        "    for i in range(n):\n"
        "        for j in range(0, n - i - 1):\n"
        "            if arr[j] > arr[j + 1]:\n"
        "                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
        "    return arr\n"
    ),
    "merge_sort": (
        "def merge_sort(arr):\n"
        "    if len(arr) <= 1:\n"
        "        return arr\n"
        "    mid = len(arr) // 2\n"
        "    left = merge_sort(arr[:mid])\n"
        "    right = merge_sort(arr[mid:])\n"
        "    out = []\n"
        "    i = j = 0\n"
        "    while i < len(left) and j < len(right):\n"
        "        if left[i] <= right[j]:\n"
        "            out.append(left[i]); i += 1\n"
        "        else:\n"
        "            out.append(right[j]); j += 1\n"
        "    out.extend(left[i:]); out.extend(right[j:])\n"
        "    return out\n"
    ),
    "gcd": (
        "def gcd(a, b):\n"
        "    while b:\n"
        "        a, b = b, a % b\n"
        "    return a\n"
    ),
    "is_prime": (
        "def is_prime(n):\n"
        "    if n < 2:\n"
        "        return False\n"
        "    i = 2\n"
        "    while i * i <= n:\n"
        "        if n % i == 0:\n"
        "            return False\n"
        "        i += 1\n"
        "    return True\n"
    ),
    "levenshtein": (
        "def levenshtein(a, b):\n"
        "    m, n = len(a), len(b)\n"
        "    dp = list(range(n + 1))\n"
        "    for i in range(1, m + 1):\n"
        "        prev = dp[0]\n"
        "        dp[0] = i\n"
        "        for j in range(1, n + 1):\n"
        "            cur = dp[j]\n"
        "            cost = 0 if a[i - 1] == b[j - 1] else 1\n"
        "            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)\n"
        "            prev = cur\n"
        "    return dp[n]\n"
    ),
    "rle_encode": (
        "def rle_encode(data):\n"
        "    if not data:\n"
        "        return []\n"
        "    out = []\n"
        "    count = 1\n"
        "    for i in range(1, len(data)):\n"
        "        if data[i] == data[i - 1]:\n"
        "            count += 1\n"
        "        else:\n"
        "            out.append((data[i - 1], count))\n"
        "            count = 1\n"
        "    out.append((data[-1], count))\n"
        "    return out\n"
    ),
    "token_bucket": (
        "class TokenBucket:\n"
        "    def __init__(self, rate, capacity):\n"
        "        self.rate = rate\n"
        "        self.capacity = capacity\n"
        "        self.tokens = capacity\n"
        "        self.last = 0.0\n"
        "    def consume(self, want):\n"
        "        now = self.now()\n"
        "        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)\n"
        "        self.last = now\n"
        "        if self.tokens >= want:\n"
        "            self.tokens -= want\n"
        "            return True\n"
        "        return False\n"
    ),
    "lru_cache_impl": (
        "class LRUCache:\n"
        "    def __init__(self, size):\n"
        "        self.size = size\n"
        "        self.store = {}\n"
        "        self.order = []\n"
        "    def get(self, key):\n"
        "        if key not in self.store:\n"
        "            return None\n"
        "        self.order.remove(key)\n"
        "        self.order.append(key)\n"
        "        return self.store[key]\n"
        "    def put(self, key, value):\n"
        "        if key in self.store:\n"
        "            self.order.remove(key)\n"
        "        elif len(self.store) >= self.size:\n"
        "            old = self.order.pop(0)\n"
        "            del self.store[old]\n"
        "        self.store[key] = value\n"
        "        self.order.append(key)\n"
    ),
    "top_k_heap": (
        "import heapq\n"
        "\n"
        "def top_k(items, k):\n"
        "    heap = []\n"
        "    for it in items:\n"
        "        heapq.heappush(heap, it)\n"
        "        if len(heap) > k:\n"
        "            heapq.heappop(heap)\n"
        "    return sorted(heap, reverse=True)\n"
    ),
    "rabin_karp": (
        "def rabin_karp(text, pattern):\n"
        "    m, n = len(pattern), len(text)\n"
        "    if m > n:\n"
        "        return -1\n"
        "    base, mod = 31, 1000003\n"
        "    target = 0\n"
        "    for ch in pattern:\n"
        "        target = (target * base + ord(ch)) % mod\n"
        "    rolling = 0\n"
        "    for i in range(n):\n"
        "        rolling = (rolling * base + ord(text[i])) % mod\n"
        "        if i >= m:\n"
        "            rolling = (rolling - ord(text[i - m]) * pow(base, m - 1, mod)) % mod\n"
        "        if rolling == target and text[i - m + 1 : i + 1] == pattern:\n"
        "            return i - m + 1\n"
        "    return -1\n"
    ),
    "union_find": (
        "class UnionFind:\n"
        "    def __init__(self, n):\n"
        "        self.parent = list(range(n))\n"
        "        self.rank = [0] * n\n"
        "    def find(self, x):\n"
        "        while self.parent[x] != x:\n"
        "            self.parent[x] = self.parent[self.parent[x]]\n"
        "            x = self.parent[x]\n"
        "        return x\n"
        "    def union(self, a, b):\n"
        "        ra, rb = self.find(a), self.find(b)\n"
        "        if ra == rb:\n"
        "            return False\n"
        "        if self.rank[ra] < self.rank[rb]:\n"
        "            ra, rb = rb, ra\n"
        "        self.parent[rb] = ra\n"
        "        if self.rank[ra] == self.rank[rb]:\n"
        "            self.rank[ra] += 1\n"
        "        return True\n"
    ),
    "sieve_primes": (
        "def sieve_primes(limit):\n"
        "    if limit < 2:\n"
        "        return []\n"
        "    mark = bytearray([1]) * (limit + 1)\n"
        "    mark[0] = mark[1] = 0\n"
        "    p = 2\n"
        "    while p * p <= limit:\n"
        "        if mark[p]:\n"
        "            for m in range(p * p, limit + 1, p):\n"
        "                mark[m] = 0\n"
        "        p += 1\n"
        "    return [i for i in range(2, limit + 1) if mark[i]]\n"
    ),
    "inorder_walk": (
        "def inorder_walk(root):\n"
        "    out = []\n"
        "    stack = []\n"
        "    cur = root\n"
        "    while stack or cur:\n"
        "        while cur:\n"
        "            stack.append(cur)\n"
        "            cur = cur.left\n"
        "        cur = stack.pop()\n"
        "        out.append(cur.val)\n"
        "        cur = cur.right\n"
        "    return out\n"
    ),
    "shunting_yard": (
        "def shunting_yard(tokens):\n"
        "    prec = {\"+\": 1, \"-\": 1, \"*\": 2, \"/\": 2}\n"
        "    out = []\n"
        "    ops = []\n"
        "    for tok in tokens:\n"
        "        if tok.isdigit():\n"
        "            out.append(tok)\n"
        "        elif tok == \"(\":\n"
        "            ops.append(tok)\n"
        "        elif tok == \")\":\n"
        "            while ops and ops[-1] != \"(\":\n"
        "                out.append(ops.pop())\n"
        "            ops.pop()\n"
        "        else:\n"
        "            while ops and ops[-1] != \"(\" and prec.get(ops[-1], 0) >= prec.get(tok, 0):\n"
        "                out.append(ops.pop())\n"
        "            ops.append(tok)\n"
        "    while ops:\n"
        "        out.append(ops.pop())\n"
        "    return out\n"
    ),
    "huffman_freq": (
        "def huffman_freq(data):\n"
        "    freq = {}\n"
        "    for ch in data:\n"
        "        freq[ch] = freq.get(ch, 0) + 1\n"
        "    leaves = sorted(freq.items(), key=lambda kv: kv[1])\n"
        "    while len(leaves) > 1:\n"
        "        a = leaves.pop(0)\n"
        "        b = leaves.pop(0)\n"
        "        merged = (None, a[1] + b[1])\n"
        "        leaves.append(merged)\n"
        "        leaves.sort(key=lambda kv: kv[1])\n"
        "    return freq\n"
    ),
    "exponential_backoff": (
        "def exponential_backoff(attempt, base=1.0, cap=30.0):\n"
        "    delay = base * (2 ** attempt)\n"
        "    if delay > cap:\n"
        "        delay = cap\n"
        "    jitter = delay * 0.1\n"
        "    return delay + (jitter % 0.5)\n"
    ),
    "json_flatten": (
        "def json_flatten(obj, prefix=\"\"):\n"
        "    out = {}\n"
        "    for key, val in obj.items():\n"
        "        path = f\"{prefix}.{key}\" if prefix else key\n"
        "        if isinstance(val, dict):\n"
        "            out.update(json_flatten(val, path))\n"
        "        else:\n"
        "            out[path] = val\n"
        "    return out\n"
    ),
}


def detect_license(pkg: str) -> "str | None":
    """从包元数据检测真实 SPDX 许可证（优先 License-Expression，其次短 License，
    再次 OSI 分类器兜底）。返回规范化 SPDX 标识或 None。"""
    try:
        md = _md.metadata(pkg)
    except Exception:
        return None
    lic_expr = (md.get("License-Expression") or "").strip()
    if lic_expr and len(lic_expr) < 160:
        return lic_expr
    lic_field = (md.get("License") or "").strip()
    if lic_field and len(lic_field) < 80 and re.fullmatch(
        r"[A-Za-z0-9.\-+ ]+( AND | OR |\(|\))*[A-Za-z0-9.\-+]+", lic_field
    ):
        return lic_field
    for clf in md.get_all("Classifier") or []:
        if clf.startswith("License :: OSI Approved ::"):
            name = clf.split("::")[-1].strip()
            if name in _CLASSIFIER_TO_SPDX:
                return _CLASSIFIER_TO_SPDX[name]
    return None


def expected_compat(license_str: "str | None") -> str:
    """用流水线的同一 OSADL 矩阵计算 片段许可证 vs MIT 参考项目 的兼容性结论。"""
    if not license_str:
        return "NEEDS_REVIEW"
    comp = _is_compat(_lic_norm(license_str), _lic_norm(PROJECT_LICENSE))
    return _COMPAT_MAP.get(comp, "NEEDS_REVIEW")


# ---------- tree-sitter 辅助 ----------
def _walk(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        children = getattr(n, "named_children", None)
        if children is None:
            children = getattr(n, "children", None)
        if children:
            stack.extend(children)


def _slice(node, raw: bytes) -> str:
    """按字节切片实体源码；若被 decorated_definition 包裹则包含装饰器。"""
    start = node.start_byte
    parent = node.parent
    if parent is not None and parent.type == "decorated_definition":
        start = parent.start_byte
    return raw[start : node.end_byte].decode("utf-8", errors="replace")


def _node_name(node, raw: bytes) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return ""
    return raw[name_node.start_byte : name_node.end_byte].decode("utf-8", errors="replace")


def _is_docstring(node) -> bool:
    if node.type != "expression_statement":
        return False
    inner = getattr(node, "named_children", None) or getattr(node, "children", None) or []
    return bool(inner) and inner[0].type in ("string", "concatenated_string")


def _named_body(node):
    body = node.child_by_field_name("body")
    if body is None:
        return []
    children = getattr(body, "named_children", None) or getattr(body, "children", None) or []
    return [c for c in children if c.type != "comment"]


def collect_entities(py_path: Path, parser) -> "tuple[list, list]":
    """解析单个文件，返回 (函数实体列表, 类实体列表)。"""
    raw = py_path.read_bytes()
    try:
        tree = parser.parse(raw)
    except Exception:
        return [], []
    funcs: list[dict] = []
    classes: list[dict] = []
    for node in _walk(tree.root_node):
        if node.type == "function_definition":
            name = _node_name(node, raw)
            if not name or name.startswith("__") or name in COMMON_NAMES:
                continue
            body = _named_body(node)
            if not (5 <= len(body) <= 40):
                continue
            funcs.append({"kind": "func", "name": name, "src": _slice(node, raw), "n": len(body)})
        elif node.type == "class_definition":
            name = _node_name(node, raw)
            if not name:
                continue
            body = [c for c in _named_body(node) if not _is_docstring(c)]
            if len(body) < 2:
                continue
            classes.append({"kind": "class", "name": name, "src": _slice(node, raw), "n": len(body)})
    return funcs, classes


def _iter_py_files(pkg_dir: Path):
    for py in sorted(pkg_dir.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        if any(p in ("tests", "test") for p in py.parts):
            continue
        try:
            size = py.stat().st_size
        except OSError:
            continue
        if not (_MIN_FILE <= size <= _MAX_FILE):
            continue
        yield py


def _sanitize(name: str) -> str:
    """实体名 → 小写文件名基（Windows NTFS 大小写不敏感，统一小写避免冲突）。"""
    return re.sub(r"\W+", "_", name).lower() or "entity"


def _unique_fname(base: str, used: "set[str]") -> str:
    """包内小写去重文件名基（防 MinHash.py / minhash.py 互相覆盖）。"""
    if base not in used:
        used.add(base)
        return base
    k = 2
    while f"{base}_{k}" in used:
        k += 1
    used.add(f"{base}_{k}")
    return f"{base}_{k}"


def extract_package(pkg: str, parser) -> "tuple[list, list, str | None]":
    """提取单个包的函数/类实体。返回 (funcs, classes, license)。

    源码定位：优先本机已安装包（importlib），其次 ``data/raw_sources/<pkg>``
    （PyPI wheel 解压归档，供未安装的 GPL/LGPL/MPL 真实包复用）。
    """
    spec = _util.find_spec(pkg)
    if spec is not None and spec.origin:
        pkg_dir = Path(spec.origin).parent
    else:
        raw_dir = ROOT / "data" / "raw_sources" / pkg / pkg
        if raw_dir.exists():
            pkg_dir = raw_dir
        else:
            logging.warning("无法定位包 %s 源码（未安装且无归档），跳过", pkg)
            return [], [], None
    if not pkg_dir.exists():
        return [], [], None
    lic = (
        REPRESENTATIVE_LICENSE.get(pkg)
        or RAW_PACKAGE_LICENSES.get(pkg)
        or detect_license(pkg)
    )
    seen_f, seen_c = set(), set()
    funcs, classes = [], []
    for py in _iter_py_files(pkg_dir):
        fs, cs = collect_entities(py, parser)
        for e in fs:
            if e["name"] in seen_f:
                continue
            seen_f.add(e["name"])
            funcs.append(e)
        for e in cs:
            if e["name"] in seen_c:
                continue
            seen_c.add(e["name"])
            classes.append(e)
    # 按实体规模降序取预算
    funcs.sort(key=lambda e: e["n"], reverse=True)
    classes.sort(key=lambda e: e["n"], reverse=True)
    return funcs[:FUNCS_PER_PKG], classes[:CLASSES_PER_PKG], lic


def select_negatives(all_entities: "list[dict]", n: int = 8) -> "list[tuple[str, str]]":
    """从负样本池选取**确定性零匹配**的样本：对每个候选，用流水线同款确定性
    验证器（L1 规范型 / L2 结构包含 / L3 锚点游程）逐一比对全部 KB 实体，
    任一实体命中即视为「与 KB 有克隆证据」而跳过。保证负样本在决策路径上
    与任何 KB 实体都不构成克隆（不止锚点游程，也覆盖单语句 L2 过度匹配等
    全部确定性判定路径）。
    """
    out: list[tuple[str, str]] = []
    for name, code in NEG_POOL.items():
        if any(
            _verify(e["src"], code, code.splitlines(), e["src"].splitlines())
            for e in all_entities
        ):
            continue
        out.append((name, code))
        if len(out) >= n:
            break
    return out


def build_benchmark(
    bench: Path,
    *,
    extra_projects: "dict[str, dict] | None" = None,
    target_packages: "list[str] | None" = None,
) -> None:
    """构建真实语料基准到 ``bench`` 目录（可复用：混合许可证基准注入干扰项目）。

    ``extra_projects``：{项目名: {"license": SPDX, "entities": [{kind,name,src,n}...]}}，
    这些项目只进 KB（写实体文件 + licenses.json + 参与负样本零匹配过滤），
    不生成查询——供 benchmark_mixed 注入 GPL/MPL/LGPL 干扰实体量化误报下降。
    ``target_packages``：覆盖目标包列表（默认全局 TARGET_PACKAGES）——混合基准
    传原 6 包，避免 GPL/LGPL/MPL 目标包与干扰项目重叠。
    """
    if not _TS_OK:
        raise RuntimeError("tree-sitter 不可用，无法提取真实语料")
    parser = _ts.Parser(_TSL)

    kb_dir = bench / "kb"
    proj_dir = kb_dir / "projects"
    query_dir = bench / "queries"
    for d in (proj_dir, query_dir):
        d.mkdir(parents=True, exist_ok=True)
    (kb_dir / ".index").mkdir(parents=True, exist_ok=True)

    # 1) 提取各包实体并分配包内唯一文件名
    licenses: dict[str, str] = {}
    pkg_entities: dict[str, list[dict]] = {}
    all_entities: list[dict] = []
    for pkg in (target_packages if target_packages is not None else TARGET_PACKAGES):
        funcs, classes, lic = extract_package(pkg, parser)
        if lic is None:
            lic = "UNKNOWN"
        if not funcs and not classes:
            logging.warning("包 %s 未提取到实体，跳过", pkg)
            continue
        licenses[pkg] = lic
        used: set[str] = set()
        entities: list[dict] = []
        for e in funcs + classes:
            e = dict(e)
            e["fname"] = _unique_fname(_sanitize(e["name"]), used)
            entities.append(e)
        pkg_entities[pkg] = entities
        all_entities.extend(entities)

    # 1.5) 注入干扰项目（只进 KB，不生成查询）
    extra_pkgs: set[str] = set((extra_projects or {}).keys())
    for proj, info in (extra_projects or {}).items():
        lic = (info.get("license") or "UNKNOWN").strip() or "UNKNOWN"
        licenses[proj] = lic
        used: set[str] = set()
        ents: list[dict] = []
        for e in info.get("entities", []):
            e = dict(e)
            e["fname"] = _unique_fname(_sanitize(e.get("name") or proj), used)
            ents.append(e)
        pkg_entities[proj] = ents
        all_entities.extend(ents)

    # 2) 负样本（确定性验证器零匹配过滤，覆盖真实 + 干扰全部实体）
    negatives = select_negatives(all_entities, 8)

    # 3) 写 KB 实体文件（真实 + 干扰）
    for pkg, entities in pkg_entities.items():
        (proj_dir / pkg).mkdir(parents=True, exist_ok=True)
        for e in entities:
            (proj_dir / pkg / f"{e['fname']}.py").write_text(e["src"], encoding="utf-8")

    # 4) 生成查询 + ground_truth（仅真实项目）
    ground_truth: list[dict] = []
    qid = 0
    stats: dict[str, dict] = {}

    for pkg, entities in pkg_entities.items():
        if pkg in extra_pkgs:
            continue  # 干扰项目不生成查询
        exp_compat = expected_compat(licenses[pkg])
        nf = nc = 0
        for e in entities:
            base = e["fname"]
            if e["kind"] == "func":
                # exact
                qid += 1
                nm = f"q{qid:03d}_exact_{pkg}_{base}.py"
                (query_dir / nm).write_text(e["src"], encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "exact", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nf += 1
                ren = _renamed(e["src"], qid)
                if ren != e["src"]:
                    qid += 1
                    nm = f"q{qid:03d}_renamed_{pkg}_{base}.py"
                    (query_dir / nm).write_text(ren, encoding="utf-8")
                    ground_truth.append({"id": nm, "kind": "renamed", "expected_project": pkg,
                                         "expected_license": licenses[pkg], "expected_compat": exp_compat})
                    nf += 1
                qid += 1
                nm = f"q{qid:03d}_transformed_{pkg}_{base}.py"
                (query_dir / nm).write_text(_transformed(e["src"], qid), encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "transformed", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nf += 1
                qid += 1
                nm = f"q{qid:03d}_deleted_{pkg}_{base}.py"
                (query_dir / nm).write_text(_stmt_deleted(e["src"], qid), encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "deleted", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nf += 1
                qid += 1
                nm = f"q{qid:03d}_reordered_{pkg}_{base}.py"
                (query_dir / nm).write_text(_stmt_reordered(e["src"], qid), encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "reordered", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nf += 1
            else:
                # 类实体：exact / transformed / class_attr（L2b）
                qid += 1
                nm = f"q{qid:03d}_exact_{pkg}_{base}.py"
                (query_dir / nm).write_text(e["src"], encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "exact", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nc += 1
                qid += 1
                nm = f"q{qid:03d}_transformed_{pkg}_{base}.py"
                (query_dir / nm).write_text(_transformed(e["src"], qid), encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "transformed", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nc += 1
                qid += 1
                nm = f"q{qid:03d}_class_attr_{pkg}_{base}.py"
                (query_dir / nm).write_text(_class_attr_clone(e["src"], qid), encoding="utf-8")
                ground_truth.append({"id": nm, "kind": "class_attr", "expected_project": pkg,
                                     "expected_license": licenses[pkg], "expected_compat": exp_compat})
                nc += 1

        n_f_entities = sum(1 for e in entities if e["kind"] == "func")
        n_c_entities = sum(1 for e in entities if e["kind"] == "class")
        stats[pkg] = {"license": licenses[pkg], "funcs": n_f_entities,
                      "classes": n_c_entities, "variants": nf + nc}

    # 负样本
    for name, code in negatives:
        qid += 1
        nm = f"q{qid:03d}_negative_{name}.py"
        (query_dir / nm).write_text(code, encoding="utf-8")
        ground_truth.append({"id": nm, "kind": "negative", "expected_project": None,
                             "expected_license": None, "expected_compat": "COMPATIBLE"})

    (kb_dir / "licenses.json").write_text(
        json.dumps(licenses, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (bench / "ground_truth.json").write_text(
        json.dumps({"project_license": PROJECT_LICENSE, "kb_path": str(kb_dir),
                    "queries": ground_truth}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    n_pos = sum(1 for g in ground_truth if g["kind"] != "negative")
    n_neg = sum(1 for g in ground_truth if g["kind"] == "negative")
    print("=" * 64)
    print("真实语料基准生成完成 ->", bench)
    print("=" * 64)
    for pkg, s in stats.items():
        print(f"  {pkg:18s} license={s['license']:14s} funcs={s['funcs']} classes={s['classes']} variants={s['variants']}")
    if extra_pkgs:
        for p in sorted(extra_pkgs):
            print(f"  [干扰] {p:16s} license={licenses[p]}")
    print(f"  负样本: {n_neg} (确定性验证器零匹配过滤后)")
    print("-" * 64)
    print(f"KB 项目: {len(licenses)}  查询: {len(ground_truth)} (positive={n_pos}, negative={n_neg})")


def main() -> None:
    build_benchmark(BENCH)


if __name__ == "__main__":
    main()
