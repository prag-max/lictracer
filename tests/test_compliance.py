# -*- coding: utf-8 -*-
"""合规推理层单元测试：COMPATIBLE / INCOMPATIBLE / NEEDS_REVIEW。"""
import datetime as _dt
import logging

import src.compliance.matrix_loader as ml
from src.compliance.matrix_loader import is_compatible, snapshot_staleness_months
from src.compliance.rule_engine import evaluate


def _seg(source, lic, start, end, score=0.9):
    return {
        "id": 1,
        "lines": f"{start}-{end}",
        "line_start": start,
        "line_end": end,
        "source": source,
        "license": lic,
        "score": score,
    }


def test_mit_project_with_gpl_segment_is_incompatible():
    segments = [_seg("finance-lib", "GPL-3.0", 6, 7)]
    result = evaluate(segments, "MIT")
    assert result["status"] == "INCOMPATIBLE"
    assert result["risk_level"] == "HIGH"
    assert "GPL-3.0" in result["reason"]


def test_all_mit_is_compatible():
    segments = [_seg("requests", "MIT", 2, 3)]
    result = evaluate(segments, "MIT")
    assert result["status"] == "COMPATIBLE"
    assert result["risk_level"] == "LOW"


def test_unknown_license_needs_review():
    segments = [_seg("custom", "Proprietary-Custom", 1, 2)]
    result = evaluate(segments, "MIT")
    assert result["status"] == "NEEDS_REVIEW"


def test_gpl_variant_normalization():
    # GPL-3.0-only 应与 GPL-3.0 归一，同样触发 INCOMPATIBLE
    segments = [_seg("finance-lib", "GPL-3.0-only", 6, 7)]
    result = evaluate(segments, "MIT")
    assert result["status"] == "INCOMPATIBLE"


# ---------- 复合许可证表达式（OR / AND） ----------
def test_or_expression_any_compatible_is_yes():
    # MIT OR GPL-3.0-only：可选 MIT，与项目 MIT 兼容 → YES
    assert is_compatible("MIT OR GPL-3.0-only", "MIT") == "YES"


def test_or_expression_all_incompatible_is_no():
    # GPL-2.0-only OR GPL-3.0-only：均与项目 MIT 不兼容 → NO
    assert is_compatible("GPL-2.0-only OR GPL-3.0-only", "MIT") == "NO"


def test_and_expression_any_incompatible_is_no():
    # Apache-2.0 AND GPL-3.0-only：须同时满足，GPL 成分不兼容 → NO
    assert is_compatible("Apache-2.0 AND GPL-3.0-only", "MIT") == "NO"


def test_and_expression_all_compatible_is_yes():
    # MIT AND BSD-3-Clause：均与项目 MIT 兼容 → YES
    assert is_compatible("MIT AND BSD-3-Clause", "MIT") == "YES"


def test_parenthesized_expression():
    # (Apache-2.0 OR MIT) AND BSD-3-Clause → 与 MIT 项目兼容
    assert is_compatible("(Apache-2.0 OR MIT) AND BSD-3-Clause", "MIT") == "YES"


def test_compound_expression_in_rule_engine():
    # 端到端：OR 表达式中存在兼容选项 → 不判定为 INCOMPATIBLE
    segments = [_seg("hybrid", "MIT OR GPL-3.0", 1, 2)]
    result = evaluate(segments, "MIT")
    assert result["status"] != "INCOMPATIBLE"


# ---------- OSADL 快照时效告警（离线、确定性，today 注入） ----------
def test_snapshot_staleness_months_calculation():
    assert snapshot_staleness_months(_dt.date(2024, 5, 22)) == 0
    assert snapshot_staleness_months(_dt.date(2025, 1, 1)) == 8
    assert snapshot_staleness_months(_dt.date(2025, 5, 22)) == 12
    assert snapshot_staleness_months(_dt.date(2026, 8, 23)) == 27


def test_warn_fires_once_after_threshold(monkeypatch, caplog):
    monkeypatch.setattr(ml, "_snapshot_warned", False)
    with caplog.at_level(logging.WARNING, logger="lictracer.compliance"):
        first = ml.warn_if_osadl_snapshot_stale(today=_dt.date(2026, 8, 23))
        second = ml.warn_if_osadl_snapshot_stale(today=_dt.date(2026, 8, 23))
    assert first is True
    assert second is False  # 每进程至多一次
    assert "OSADL" in caplog.text and "快照" in caplog.text


def test_warn_silent_before_threshold(monkeypatch):
    monkeypatch.setattr(ml, "_snapshot_warned", False)
    assert ml.warn_if_osadl_snapshot_stale(today=_dt.date(2025, 1, 1)) is False
