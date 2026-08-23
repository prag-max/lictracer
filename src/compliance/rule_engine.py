# -*- coding: utf-8 -*-
"""合规推理层 —— 规则引擎主入口，输出确定性结论。

判定逻辑：
- 逐片段把许可证标准化，再查 OSADL 矩阵得到与项目整体许可证的兼容性；
- 存在 "NO" 且该片段为 GPL 系列（copyleft）→ 强化为 INCOMPATIBLE 并标注传染；
- 存在 "NO" 但非 copyleft → INCOMPATIBLE；
- 存在 "UNKNOWN" → NEEDS_REVIEW；
- 全部 "YES" → COMPATIBLE。
整个过程确定性、可复现，并输出推演步骤证据链（steps）。
"""
from __future__ import annotations

from src.compliance.copyleft_engine import assess, is_copyleft
from src.compliance.license_normalizer import normalize
from src.compliance.matrix_loader import is_compatible


def evaluate(segments: "list[dict]", project_license: str, link_type: str = "dynamic") -> dict:
    """合规推理主入口。

    segments: 聚合层输出的片段列表 [{id, lines, source, license, score, ...}]。
    project_license: 项目整体许可证。
    返回 {status, risk_level, reason, steps, segments}。
    """
    proj_norm = normalize(project_license)
    steps = []
    annotated = []
    compat_flags = []

    for idx, seg in enumerate(segments, start=1):
        seg_license_raw = seg.get("license", "UNKNOWN")
        seg_norm = normalize(seg_license_raw)
        comp = is_compatible(seg_norm, proj_norm)
        cop = is_copyleft(seg_norm)
        assess_result = assess(seg_norm, link_type=link_type) if cop else {"copyleft": False}

        compat_flags.append(comp)

        steps.append(
            {
                "step": idx,
                "segment_id": seg.get("id"),
                "source": seg.get("source"),
                "license": seg_license_raw,
                "normalized_license": seg_norm,
                "project_license": proj_norm,
                "compatibility": comp,
                "copyleft": cop,
                "description": _describe_step(seg, seg_norm, proj_norm, comp, cop, assess_result),
            }
        )

        seg_out = dict(seg)
        seg_out["normalized_license"] = seg_norm
        seg_out["compatibility"] = comp
        seg_out["copyleft"] = cop
        annotated.append(seg_out)

    status, risk_level = _decide(compat_flags, annotated)
    reason = _build_reason(status, annotated, proj_norm, assess, link_type)

    return {
        "status": status,
        "risk_level": risk_level,
        "reason": reason,
        "steps": steps,
        "segments": annotated,
    }


def _decide(compat_flags: "list[str]", annotated: "list[dict]"):
    if "NO" in compat_flags:
        return "INCOMPATIBLE", "HIGH"
    if "UNKNOWN" in compat_flags:
        return "NEEDS_REVIEW", "MEDIUM"
    return "COMPATIBLE", "LOW"


def _describe_step(seg, seg_norm, proj_norm, comp, cop, assess_result):
    if comp == "NO":
        if cop:
            return (
                f"片段#{seg.get('id')}（来源 {seg.get('source')}）许可证 {seg_norm} 与项目整体许可证 "
                f"{proj_norm} 不兼容，且 {seg_norm} 具有 Copyleft 传染性："
                f"{assess_result.get('description', '')}"
            )
        return (
            f"片段#{seg.get('id')}（来源 {seg.get('source')}）许可证 {seg_norm} 与项目整体许可证 "
            f"{proj_norm} 不兼容。"
        )
    if comp == "UNKNOWN":
        return (
            f"片段#{seg.get('id')}（来源 {seg.get('source')}）许可证 {seg_norm} 与项目整体许可证 "
            f"{proj_norm} 的兼容性无法确定，需人工复核。"
        )
    return f"片段#{seg.get('id')}（来源 {seg.get('source')}）许可证 {seg_norm} 与项目整体许可证 {proj_norm} 兼容。"


def _build_reason(status, annotated, proj_norm, assess, link_type):
    if status == "COMPATIBLE":
        return f"所有 {len(annotated)} 个片段均与项目整体许可证 {proj_norm} 兼容。"

    if status == "INCOMPATIBLE":
        bad = [s for s in annotated if s.get("compatibility") == "NO"]
        copyleft_bad = [s for s in bad if s.get("copyleft")]
        details = []
        for s in bad:
            lic = s.get("normalized_license")
            if s.get("copyleft"):
                a = assess(lic, link_type=link_type)
                details.append(f"{lic}（来源 {s.get('source')}，Copyleft 传染：{a.get('action')}）")
            else:
                details.append(f"{lic}（来源 {s.get('source')}）")
        if copyleft_bad:
            return (
                "存在 " + "、".join(details) + f"与项目整体许可证 {proj_norm} 不兼容，"
                f"且其中包含 Copyleft 许可证，具有传染性，整体判定为 INCOMPATIBLE。"
            )
        return "存在 " + "、".join(details) + f"与项目整体许可证 {proj_norm} 不兼容，判定为 INCOMPATIBLE。"

    unknown = [s for s in annotated if s.get("compatibility") == "UNKNOWN"]
    licenses = "、".join(sorted({s.get("normalized_license", "UNKNOWN") for s in unknown}))
    return f"存在片段许可证 {licenses} 与项目整体许可证 {proj_norm} 的兼容性无法确定，需人工复核。"


# 别名，保持接口简洁
rule_engine_entry = evaluate
