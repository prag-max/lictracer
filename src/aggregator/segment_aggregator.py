# -*- coding: utf-8 -*-
"""多源聚合层 —— 把多方证据按行号聚类，拆分不同来源片段。

本版语义（为主证据融合提供一致输入）：
- **异源证据永不合并**：不同来源（不同 project）即使重叠 / 相邻也各自成段——
  保证每段单一来源、归属一致，避免「把不同来源证据吸收进一段并只保留一个
  来源」导致正确来源被掩盖（真实跨项目场景下，弱结构伪匹配与正确来源重叠
  时尤其关键）；
- 同源证据允许中间隔 <=3 行合并（同一函数内零星空隙），score 取该来源证据的
  最高相似度、verification_level 取最强（数值最小）者——同一来源的
  source / license / score / verification_level 天然一致；
- 片段按行号排序后从 1 编号。
"""
from __future__ import annotations


def _new_segment(ev: dict) -> dict:
    return {
        "line_start": ev["line_start"],
        "line_end": ev["line_end"],
        "source": ev.get("project"),
        "license": ev.get("license"),
        "score": ev.get("similarity", 0.0),
        "verification_level": ev.get("verification_level"),
    }


def aggregate(evidence_list: "list[dict]") -> "list[dict]":
    """按行号聚类证据，输出 [{id, lines, line_start, line_end, source, license, score, verification_level}]。

    规则：
    - 仅**同一来源**且间隔 <=3 行的证据合并为同一片段；
    - 异源证据（重叠或相邻）各自成段，来源 / 许可证独立可见；
    - 同源合并后 score 取最高相似度、verification_level 取最强（min）；
    - 片段按行号排序后从 1 编号。
    """
    if not evidence_list:
        return []

    sorted_ev = sorted(evidence_list, key=lambda e: (e["line_start"], e["line_end"]))

    raw_segments = []
    for ev in sorted_ev:
        if not raw_segments:
            raw_segments.append(_new_segment(ev))
            continue

        cur = raw_segments[-1]
        gap = ev["line_start"] - cur["line_end"]
        same_source = ev.get("project") == cur["source"]
        # 仅同源合并（异源不合并：保持每段单一来源，归属一致）
        if same_source and gap <= 3:
            cur["line_start"] = min(cur["line_start"], ev["line_start"])
            cur["line_end"] = max(cur["line_end"], ev["line_end"])
            if ev.get("similarity", 0.0) > cur["score"]:
                cur["score"] = ev["similarity"]
            lvl = ev.get("verification_level")
            if lvl is not None:
                cur["verification_level"] = min(
                    cur.get("verification_level") or 99, lvl
                )
        else:
            raw_segments.append(_new_segment(ev))

    result = []
    for idx, seg in enumerate(raw_segments, start=1):
        start, end = seg["line_start"], seg["line_end"]
        lines = f"{start}-{end}" if start != end else str(start)
        result.append(
            {
                "id": idx,
                "lines": lines,
                "line_start": start,
                "line_end": end,
                "source": seg["source"],
                "license": seg["license"],
                "score": seg["score"],
                "verification_level": seg.get("verification_level"),
            }
        )
    return result
