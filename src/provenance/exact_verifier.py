# -*- coding: utf-8 -*-
r"""确定性等价验证器 —— 用布尔判定替代相似度阈值（threshold-free）。

背景：旧的端到端克隆判定依赖两个浮点阈值（redup 行级 0.5、结构兜底 0.30），
阈值由受控基准的相似度间隙拟合，在真实语料上无泛化保证。本模块把「是否为
同一份拷贝」从「相似度 ≥ T」改为三级**确定性布尔判定**，决策路径不含浮点阈值：

- **L1｜规范型精确相等**：对 ``normalize``（去注释 / 标识符归一）结果做
  ``VAR_n/FUNC_n → ID`` 占位并折叠空白，得到与重命名/空白/注释无关的规范型；
  规范型相等 ⟺ 逐字 / 重命名克隆（T1/T2）——布尔；
- **L2｜结构语句序列包含（函数体 / 类体 / 模块级）**：tree-sitter 提取 KB 文件
  的规范化结构序列（identifier→ID、number→NUM、string→STR 占位），分三类：
  - 函数体：函数定义内完整语句序列（T3 near-miss 改写，噪声可插任意位置）；
  - 类体：``class`` 的类属性赋值 + 方法**签名**（不含方法体）——T5 类属性 /
    配置类克隆，复制并改名方法仍保序命中，方法体改写不影响；
  - 模块级：纯模块级片段（仅 import + 顶层常量，无函数 / 类）的完整结构序列，
    保守要求 ≥ ``MIN_MODULE_STMTS`` 条以防通用 import 误报（T6 模块级克隆）；
  任一完整序列以**保序子序列**形式出现在查询对应层级即判结构克隆——布尔；
- **L3｜锚点行游程**：规范化行（行级 ID/NUM/STR 占位）的连续 L 元组
  （L = ``min_anchor_lines``，策略定义「多长算一份拷贝」）与 KB 共享即命中
  ——布尔，捕获部分拷贝 / 行级改写残留（语句删除 / 重排后仍有 ≥L 连续行）。

层次含义：L1 ⊂ L2 ⊂ L3，判定强度递减。L3 是召回闸门（过包含），L1/L2 是
精确验证。**任何命中都不再依赖相似度数值**；MinHash 相似度仅保留为候选排序
与报告展示字段。L1/L2/L3 均为确定性布尔判定（决策路径无浮点阈值）。

**诚实局限**：L2 要求 KB 结构序列**完整**按序出现在查询对应层级——「语句被
删除/重排」的改写（非纯插入）将跌出 L2（但 L3 锚点游程仍可捕获 ≥ min_anchor_lines
行连续不变的片段，故仍属确定性召回）；类体匹配要求复制类保留类属性 + 方法签名
结构（方法体改动不影响、但删属性 / 删方法签名跌出）；模块级匹配仅对「无函数 /
无类」的纯模块片段启用，避免通用 import 误报。跨行交错重排（语句 A,B,C →
A,X,B,Y,C 且行级游程 < L）将跌出 L1/L2/L3，此时若 MinHash 相似度也未进入候选集
则无法召回——这类重度交错改写与语义重写（T4）一并列入残差（文档明示，不静默判定）。
"""
from __future__ import annotations

import hashlib
import re
import zlib

from src.preprocessor.ast_normalizer import (
    PY_KEYWORDS,
    ast_statement_sequences,
    normalize,
)

# 匹配类型（稳定字符串，供报告 / 评估消费）
MATCH_EXACT = "exact_canonical"          # L1
MATCH_STRUCT = "structural_containment"  # L2
MATCH_ANCHOR = "anchor_run"              # L3

# 验证级别：数值越小确定性越强（1=精确, 2=结构, 3=锚点, 4=仅 redup 行级证据）
LEVEL_EXACT = 1
LEVEL_STRUCT = 2
LEVEL_ANCHOR = 3
LEVEL_REDUP = 4

# 模块级结构匹配的保守下限：KB 模块序列 ≥ 此条数才启用（防通用 import 误报）
MIN_MODULE_STMTS = 4

# L2b 类体结构匹配的 KB 端最小规模（整数计数、无浮点，与 MIN_MODULE_STMTS
# 同思路）：KB 类体结构元素（类属性 + 方法签名）低于此值不产生 L2b 证据——
# 空壳类（1 属性 + 1 方法签名）的完整序列「被包含」太容易，是弱伪匹配源。
MIN_L2_STMTS = 3


def canonicalize(code: str) -> str:
    """源码 → 规范型 token 流（与空白 / 注释 / 重命名无关）。

    ``normalize`` 已做去注释 + 标识符归一（VAR_n / FUNC_n）；这里再统一占位
    ``VAR_n/FUNC_n → ID`` 并按 token 折叠空白，使同结构代码（含重命名）得到
    完全相同的规范型。
    """
    skel = normalize(code)
    if not skel:
        return ""
    parts = []
    for tok in re.findall(r"\w+|\S+", skel):
        if re.fullmatch(r"(?:VAR|FUNC)_\d+", tok):
            parts.append("ID")
        else:
            parts.append(tok)
    return " ".join(parts)


def canonical_hash(code: str) -> str:
    """规范型的 SHA-256（L1 精确相等判定的稳定指纹）。"""
    return hashlib.sha256(canonicalize(code).encode("utf-8")).hexdigest()


def canonical_line(line: str) -> str:
    """单行 → 行级规范型（ID/NUM/STR 占位，关键字 / 运算符保留）。

    token 以「单词或数字或单个非空白字符」粒度切分，使 ``(name):`` 拆为
    ``( ID ) :``，避免括号 / 冒号粘连破坏重命名不变性；多字符运算符
    （``==``/``>=``）逐字符保留，运算符级差异在行级仍可见。
    """
    if not line:
        return ""
    parts = []
    for tok in re.findall(r"[A-Za-z_]\w*|\d+\.?\d*|\S", line):
        if tok in PY_KEYWORDS:
            parts.append(tok)
        elif re.fullmatch(r"\d+\.?\d*", tok):
            parts.append("NUM")
        elif tok[:1] in ("'", '"'):
            parts.append("STR")
        elif re.fullmatch(r"[A-Za-z_]\w*", tok):
            parts.append("ID")
        else:
            parts.append(tok)
    return " ".join(parts)


def _canon_line_index(lines: "list[str]") -> "list[tuple[int, str]]":
    """返回 [(原行号, 行级规范型)]，跳过空规范行（空行/纯空白不参与锚点）。"""
    out = []
    for i, ln in enumerate(lines):
        c = canonical_line(ln)
        if c:
            out.append((i, c))
    return out


def _gram_key(seq: "list[tuple[int, str]]", start: int, length: int) -> int:
    """连续规范行的 L 元组 → 稳定哈希（zlib.crc32 跨进程稳定）。"""
    h = 0
    for j in range(start, start + length):
        h = (h * 31 + zlib.crc32(seq[j][1].encode("utf-8"))) & 0xFFFFFFFF
    return h


def anchor_grams(lines: "list[str]", length: int = 3) -> "set[int]":
    """规范化行游程 L 元组的哈希集合（L3 锚点召回闸门用）。"""
    idx = _canon_line_index(lines)
    L = max(1, int(length))
    if len(idx) < L:
        return set()
    return {_gram_key(idx, i, L) for i in range(len(idx) - L + 1)}


def best_anchor_run(
    query_lines: "list[str]", kb_lines: "list[str]", min_run: int = 3
) -> "tuple[int, int, int]":
    """返回 (最长命中游程长度, 查询起行, 查询止行)；无命中返回 (0, 0, 0)。

    命中定义：查询与 KB 存在长度 ≥ min_run 的**连续**规范化行 L 元组
    （L = min_run）相同。行号为 1-based 原行号。
    """
    ql = _canon_line_index(query_lines)
    kl = _canon_line_index(kb_lines)
    L = max(1, int(min_run))
    if len(ql) < L or len(kl) < L:
        return 0, 0, 0
    kb_grams = {_gram_key(kl, i, L) for i in range(len(kl) - L + 1)}

    best = 0
    best_start = best_end = 0
    i = 0
    n = len(ql) - L + 1
    while i < n:
        if _gram_key(ql, i, L) not in kb_grams:
            i += 1
            continue
        j = i
        while j < n and _gram_key(ql, j, L) in kb_grams:
            j += 1
        run_len = j - i + L - 1  # 连续命中的规范行数
        start_line = ql[i][0] + 1
        end_line = ql[j + L - 2][0] + 1
        if run_len > best:
            best, best_start, best_end = run_len, start_line, end_line
        i = j + 1
    return best, best_start, best_end


def _contains_ordered(haystack: "list[int]", needle: "list[int]") -> bool:
    """needle 是否以**保序子序列**出现于 haystack（允许插入噪声语句）。

    贪心单趟扫描 O(n+m)：KB 函数的完整规范语句序列必须按序出现在查询中，
    中间可插入无关语句（T3 近邻改写把噪声行插在任意位置）。单条语句的
    needle 同样成立（如 ``return max(low, min(value, high))`` 的规范哈希
    足够特异）；超通用单语句（如 ``return a + b``）的过度匹配风险由
    L3/级别标注兜底，并在文档如实声明。
    """
    if not needle or len(needle) > len(haystack):
        return False
    j = 0
    for v in haystack:
        if v == needle[j]:
            j += 1
            if j == len(needle):
                return True
    return False


def structural_span(
    kb_code: str, query_code: str
) -> "tuple[bool, int, int]":
    """KB 结构序列（函数体 / 类体 / 模块级）⊆ 查询对应层级（保序）→ 结构克隆。

    返回 ``(命中?, 查询命中结构起行, 查询命中结构止行)``——行区间来自查询中
    被匹配结构的实际范围（避免整文件区间导致多源片段被聚合误合并）。
    匹配优先级：函数体(L2a) → 类体(L2b) → 模块级(L2c, 仅纯模块片段且 ≥MIN_MODULE_STMTS)。
    tree-sitter 不可用或解析失败时返回 ``(False, 0, 0)``（降级：仅 L1/L3 生效）。
    """
    kb_mod, kb_funcs, kb_classes, kb_ok = ast_statement_sequences(kb_code)
    q_mod, q_funcs, q_classes, q_ok = ast_statement_sequences(query_code)
    if not kb_ok or not q_ok:
        return False, 0, 0

    # L2a：函数体结构包含（T3 near-miss 改写）。函数体语句哈希特异（含结构），
    #      无碰撞问题；合成基准 KB 为 1–3 语句「片段风格」函数，故不设规模门槛
    if kb_funcs and q_funcs:
        for kf in kb_funcs:
            needle = [s[0] for s in kf["stmts"]]
            if not needle:
                continue
            for qf in q_funcs:
                if _contains_ordered([s[0] for s in qf["stmts"]], needle):
                    return True, qf["start"], qf["end"]

    # L2b：类体结构包含（类属性 + 方法签名；T5 类属性 / 配置类克隆）；
    #      KB 类体结构元素 ≥ MIN_L2_STMTS（防空壳类 / 无参方法签名碰撞伪匹配）
    if kb_classes and q_classes:
        for kc in kb_classes:
            if len(kc["stmts"]) < MIN_L2_STMTS:
                continue
            needle = [s[0] for s in kc["stmts"]]
            if not needle:
                continue
            for qc in q_classes:
                if _contains_ordered([s[0] for s in qc["stmts"]], needle):
                    return True, qc["start"], qc["end"]

    # L2c：模块级结构包含（仅当 KB 无函数且无类——纯模块级片段；保守阈值防误报）
    if (not kb_funcs and not kb_classes) and len(kb_mod) >= MIN_MODULE_STMTS:
        if _contains_ordered([s[0] for s in q_mod], [s[0] for s in kb_mod]):
            if q_mod:
                return True, q_mod[0][1], q_mod[-1][2]

    return False, 0, 0


def verify(
    kb_code: str,
    query_code: str,
    query_lines: "list[str]",
    kb_lines: "list[str]",
    min_anchor_lines: int = 3,
) -> "dict | None":
    """对单个 KB 文件返回确定性验证证据；无任何布尔命中返回 None。

    返回 ``{match_type, line_start, line_end, verification_level}``。
    判定顺序 L1 → L2 → L3（L1/L2 的行区间取整文件 [1, len(query_lines)]）。
    """
    if not kb_code or not query_code:
        return None
    if canonicalize(kb_code) == canonicalize(query_code):
        return {
            "match_type": MATCH_EXACT,
            "line_start": 1,
            "line_end": max(1, len(query_lines)),
            "verification_level": LEVEL_EXACT,
        }
    hit, qs, qe = structural_span(kb_code, query_code)
    if hit:
        return {
            "match_type": MATCH_STRUCT,
            "line_start": qs,
            "line_end": qe,
            "verification_level": LEVEL_STRUCT,
        }
    run_len, start, end = best_anchor_run(query_lines, kb_lines, min_anchor_lines)
    if run_len >= min_anchor_lines:
        return {
            "match_type": MATCH_ANCHOR,
            "line_start": start,
            "line_end": end,
            "verification_level": LEVEL_ANCHOR,
        }
    return None


def verify_candidates(
    candidates: "list[dict] | None",
    read_code,
    query_code: str,
    query_lines: "list[str]",
    min_anchor_lines: int = 3,
) -> "list[dict]":
    """对候选集逐文件验证，返回确定性证据列表（与 evidence 同构的 dict）。

    ``read_code`` 为可调用对象（如 ``KnowledgeBase.read_file``），输入文件路径
    返回源码文本。证据字段：file/project/license/line_start/line_end/
    similarity/match_type/verification_level。
    """
    out = []
    for c in candidates or []:
        try:
            kb_code = read_code(c["file"])
        except Exception:
            continue
        v = verify(
            kb_code,
            query_code,
            query_lines,
            kb_code.splitlines(),
            min_anchor_lines=min_anchor_lines,
        )
        if v is None:
            continue
        out.append(
            {
                "file": c["file"],
                "project": c.get("project"),
                "license": c.get("license"),
                "line_start": v["line_start"],
                "line_end": v["line_end"],
                "similarity": round(float(c.get("similarity", 0.0)), 4),
                "match_type": v["match_type"],
                "verification_level": v["verification_level"],
            }
        )
    return out
