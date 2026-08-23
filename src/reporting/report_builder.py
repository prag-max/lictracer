# -*- coding: utf-8 -*-
"""报告生成层 —— 结构化 JSON 报告（含证据链）与格式导出。"""
from __future__ import annotations

import html
import json


def build(rule_result: dict, segments: "list[dict]", evidence: "list[dict]") -> dict:
    """组装与 PRD 示例对齐的 JSON 报告结构。"""
    return {
        "summary": {
            "total_segments": len(segments),
            "risk_level": rule_result.get("risk_level", "LOW"),
            "conclusion": rule_result.get("status", "UNKNOWN"),
        },
        "segments": [
            {
                "id": s.get("id"),
                "lines": s.get("lines"),
                "source": s.get("source"),
                "license": s.get("license"),
                "similarity": s.get("score"),
                "verification_level": s.get("verification_level"),
                "is_primary": bool(s.get("is_primary")),
                "drives_conclusion": bool(s.get("drives_conclusion")),
            }
            for s in segments
        ],
        "compliance_result": {
            "status": rule_result.get("status"),
            "risk_level": rule_result.get("risk_level"),
            "reason": rule_result.get("reason"),
            "steps": rule_result.get("steps", []),
        },
        "evidence": evidence,
    }


def render(report: dict, fmt: str = "json") -> str:
    """把报告渲染为 json / markdown / html 文本。"""
    if fmt == "markdown":
        return _to_markdown(report)
    if fmt == "html":
        return _to_html(report)
    return json.dumps(report, ensure_ascii=False, indent=2)


def _to_markdown(report: dict) -> str:
    lines = []
    summary = report.get("summary", {})
    lines.append("# LicTracer 合规审计报告")
    lines.append("")
    lines.append("## 摘要")
    lines.append(f"- 片段总数：{summary.get('total_segments')}")
    lines.append(f"- 风险等级：{summary.get('risk_level')}")
    lines.append(f"- 结论：{summary.get('conclusion')}")
    lines.append("")
    lines.append("## 片段明细")
    lines.append("")
    lines.append("| # | 行号 | 来源 | 许可证 | 相似度 |")
    lines.append("|---|------|------|--------|--------|")
    for seg in report.get("segments", []):
        lines.append(
            f"| {seg.get('id')} | {seg.get('lines')} | {seg.get('source')} "
            f"| {seg.get('license')} | {seg.get('similarity')} |"
        )
    lines.append("")
    cr = report.get("compliance_result", {})
    lines.append("## 合规结论")
    lines.append("")
    lines.append(f"- 状态：{cr.get('status')}")
    lines.append(f"- 风险：{cr.get('risk_level')}")
    lines.append(f"- 原因：{cr.get('reason')}")
    if report.get("nl_summary"):
        lines.append("")
        lines.append("## 摘要说明")
        lines.append("")
        lines.append(str(report["nl_summary"]))
    return "\n".join(lines)


def _to_html(report: dict) -> str:
    summary = report.get("summary", {})
    rows = []
    for seg in report.get("segments", []):
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(seg.get('id')))}</td>"
            f"<td>{html.escape(str(seg.get('lines')))}</td>"
            f"<td>{html.escape(str(seg.get('source')))}</td>"
            f"<td>{html.escape(str(seg.get('license')))}</td>"
            f"<td>{html.escape(str(seg.get('similarity')))}</td>"
            "</tr>"
        )
    cr = report.get("compliance_result", {})
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>LicTracer 报告</title></head><body>"
        "<h1>LicTracer 合规审计报告</h1>"
        f"<h2>摘要</h2><p>片段总数：{html.escape(str(summary.get('total_segments')))}；"
        f"风险等级：{html.escape(str(summary.get('risk_level')))}；"
        f"结论：{html.escape(str(summary.get('conclusion')))}</p>"
        "<h2>片段明细</h2><table border='1' cellpadding='4'>"
        "<tr><th>#</th><th>行号</th><th>来源</th><th>许可证</th><th>相似度</th></tr>"
        + "".join(rows)
        + "</table>"
        f"<h2>合规结论</h2><p>状态：{html.escape(str(cr.get('status')))}；"
        f"风险：{html.escape(str(cr.get('risk_level')))}；"
        f"原因：{html.escape(str(cr.get('reason')))}</p>"
        "</body></html>"
    )
