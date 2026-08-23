# -*- coding: utf-8 -*-
"""合规推理层 —— OSADL 兼容性矩阵查询（使用真实 osadl-matrix 包）。

支持 **复合许可证表达式**（``OR`` / ``AND``，含括号分组）：
- ``AND``（须同时满足）：任一成分不兼容 → ``NO``；全部兼容 → ``YES``；否则 ``UNKNOWN``；
- ``OR``（可选其一）：任一成分兼容 → ``YES``；全部不兼容 → ``NO``；否则 ``UNKNOWN``。

该语义为保守合规判定：不会因「未拆分复合表达式」而把本应判定的情形错误降级为
UNKNOWN（旧行为会把 ``MIT OR GPL-3.0`` 整体交给 osadl-matrix 查询而失败）。
"""
from __future__ import annotations

import datetime as _dt
import logging
import re

from osadl_matrix import OSADLCompatibility, get_compatibility

logger = logging.getLogger("lictracer.compliance")

# ---------- OSADL 快照时效告警 ----------
# osadl-matrix 是静态快照数据包（锁定 2024.5.22.10535，即 2024-05-22 快照）：
# 新许可证不会被自动收录，须手动升版。距快照过久时在分析入口告警一次，
# 避免兼容结论基于过期数据而使用者无感知（离线、确定性，不做任何网络请求）。

OSADL_SNAPSHOT_DATE = _dt.date(2024, 5, 22)
_SNAPSHOT_WARN_MONTHS = 12
_snapshot_warned = False


def snapshot_staleness_months(today: _dt.date | None = None) -> int:
    """返回当前日期距 OSADL 快照日期的整月数（today 可注入，便于测试）。"""
    today = today or _dt.date.today()
    return (today.year - OSADL_SNAPSHOT_DATE.year) * 12 + (
        today.month - OSADL_SNAPSHOT_DATE.month
    )


def warn_if_osadl_snapshot_stale(today: _dt.date | None = None) -> bool:
    """快照距今超过 12 个月时记录 WARNING（每进程至多一次），返回是否触发告警。"""
    global _snapshot_warned
    if _snapshot_warned:
        return False
    months = snapshot_staleness_months(today)
    if months >= _SNAPSHOT_WARN_MONTHS:
        logger.warning(
            "OSADL 兼容性矩阵为 %s 快照（距今约 %d 个月）：新许可证不会自动收录，"
            "兼容结论基于该时点数据；如需覆盖新许可证请升级 osadl-matrix 包"
            "并同步 pyproject/requirements 的版本锁定。",
            OSADL_SNAPSHOT_DATE.isoformat(),
            months,
        )
        _snapshot_warned = True
        return True
    return False


def is_compatible(seg_license: str, project_license: str, matrix=None) -> str:
    """判断片段许可证与项目整体许可证的兼容性。

    osadl-matrix 方向语义：``get_compatibility(outbound, inbound)`` 中
    ``outbound`` 为“分发/整体项目”许可证，``inbound`` 为“依赖/片段”许可证。

    - 片段为复合表达式（含顶层 ``AND``/``OR``）→ 逐成分递归判定后按语义合并；
    - 否则查询矩阵，返回 ``"YES"`` / ``"NO"`` / ``"UNKNOWN"``（UNKNOWN 覆盖
      Unknown、Check dependency、Undefined 等需人工复核的情形）。
    """
    seg = (seg_license or "").strip()
    if not seg:
        return "UNKNOWN"
    return _evaluate(seg, project_license)


# ---------- 复合表达式拆分（括号感知，仅处理顶层 AND/OR） ----------

_OP_RE = re.compile(r"AND|OR")


def _strip_outer_parens(s: str) -> str:
    """反复剥离整体包裹的最外层括号（如 ``(MIT OR GPL-3.0-only)``）。"""
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        whole = True
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    whole = False
                    break
        if not whole:
            break
        s = s[1:-1].strip()
    return s


def _top_level_ops(s: str) -> "list[tuple[int, int, str]]":
    """返回括号外（深度 0）的 AND/OR 位置列表 [(start, end, op), ...]。"""
    depth = 0
    out = []
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            m = _OP_RE.match(s, i)
            if m and (i == 0 or not s[i - 1].isalnum()) and (
                m.end() >= n or not s[m.end()].isalnum()
            ):
                out.append((i, m.end(), m.group(0)))
                i = m.end()
                continue
        i += 1
    return out


def _split_at(s: str, positions: "list[tuple[int, int, str]]") -> "list[str]":
    parts = []
    prev = 0
    for start, end, _op in positions:
        parts.append(s[prev:start])
        prev = end
    parts.append(s[prev:])
    return [p.strip() for p in parts if p.strip()]


def _combine(op: str, vals: "list[str]") -> str:
    if op == "OR":
        if "YES" in vals:
            return "YES"
        if vals and all(v == "NO" for v in vals):
            return "NO"
        return "UNKNOWN"
    # AND
    if "NO" in vals:
        return "NO"
    if vals and all(v == "YES" for v in vals):
        return "YES"
    return "UNKNOWN"


def _evaluate(expr: str, project_license: str) -> str:
    """递归评估复合表达式；叶子节点查询 OSADL 矩阵。"""
    s = _strip_outer_parens(expr)
    ops = _top_level_ops(s)
    if not ops:
        return _query_matrix(s, project_license)

    # license-expression 用括号明确分组，顶层 OR 优先拆分（OR 绑定弱于 AND）
    or_ops = [o for o in ops if o[2] == "OR"]
    if or_ops:
        parts = _split_at(s, or_ops)
        return _combine("OR", [_evaluate(p, project_license) for p in parts])

    parts = _split_at(s, ops)  # 顶层全部为 AND
    return _combine("AND", [_evaluate(p, project_license) for p in parts])


def _query_matrix(seg_license: str, project_license: str) -> str:
    """单标识查询 osadl-matrix；失败/未知降级 UNKNOWN。"""
    try:
        comp = get_compatibility(project_license, seg_license)
    except Exception:
        logger.warning(
            "OSADL 兼容性查询失败（%s vs %s），降级为 UNKNOWN",
            project_license,
            seg_license,
            exc_info=True,
        )
        return "UNKNOWN"

    if comp == OSADLCompatibility.YES:
        return "YES"
    if comp == OSADLCompatibility.NO:
        return "NO"
    return "UNKNOWN"
