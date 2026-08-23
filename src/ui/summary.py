# -*- coding: utf-8 -*-
"""项目级结果聚合（纯函数、无 Qt 依赖）。

输入为 worker 产出的 entry 列表：``[{"path": Path, "report": dict|None, "error": str}]``。
聚合口径与单文件结论一致：
- 项目级状态取全部成功文件中**最严重**者（INCOMPATIBLE > NEEDS_REVIEW > COMPATIBLE）；
- 全部失败时状态为 UNKNOWN（不静默假装兼容）。
"""
from __future__ import annotations

_STATUS_SEVERITY = {"INCOMPATIBLE": 0, "NEEDS_REVIEW": 1, "COMPATIBLE": 2}
_RISK_SEVERITY = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def aggregate_project(entries) -> dict:
    """聚合批处理结果，返回项目级汇总。"""
    counts = {"INCOMPATIBLE": 0, "NEEDS_REVIEW": 0, "COMPATIBLE": 0}
    analyzed = 0
    hit_files = 0
    ambiguous: list[str] = []
    error_entries: list[dict] = []
    methodologies: list[dict] = []

    for e in entries:
        rep = e.get("report")
        if rep is None:
            error_entries.append({"path": str(e.get("path")), "error": e.get("error", "")})
            continue
        analyzed += 1
        summary = rep.get("summary") or {}
        status = summary.get("conclusion")
        if status in counts:
            counts[status] += 1
        if rep.get("segments"):
            hit_files += 1
        attr = rep.get("attribution") or {}
        if attr.get("attribution_ambiguous"):
            ambiguous.append(str(e.get("path")))
        m = rep.get("methodology")
        if isinstance(m, dict):
            methodologies.append(m)

    overall_status = "UNKNOWN"
    worst = 99
    for st, sev in _STATUS_SEVERITY.items():
        if counts[st] > 0 and sev < worst:
            worst = sev
            overall_status = st

    risk_by_status = {"INCOMPATIBLE": "HIGH", "NEEDS_REVIEW": "MEDIUM", "COMPATIBLE": "LOW"}
    overall_risk = risk_by_status.get(overall_status, "—")

    return {
        "total": len(entries),
        "analyzed": analyzed,
        "counts": counts,
        "status": overall_status,
        "risk_level": overall_risk,
        "hit_files": hit_files,
        "ambiguous": ambiguous,
        "errors": error_entries,
        "methodologies": methodologies,
    }
