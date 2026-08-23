# -*- coding: utf-8 -*-
"""主证据驱动的合规聚合：单元机制测试 + 混合许可证基准误报下降断言。

机制（src/pipeline.select_conclusion_segments）：
- 强证据段（L1/L2）参与结论；主证据段（相似度最高的已验证段）始终参与；
- 其余弱证据段（非主证据的 L3/4）仅作报告展示、不参与结论——弱伪匹配
  （真实跨项目结构近邻）携带 GPL/MPL 等高危害许可证时，旧聚合（全段参与）
  会把 COMPATIBLE 误升级为 INCOMPATIBLE / NEEDS_REVIEW（合规误报），
  新聚合消除之。

基准（evaluation/benchmark_mixed）：
KB = 真实 6 包 + 真实 GPL-2.0 / MPL-2.0 / LGPL-3.0 干扰项目（beancount /
mozinfo / python-telegram-bot 中与目标实体自然 L3 弱匹配的真实函数），
量化旧 / 新聚合的误报：旧 > 0（基线存在误报），新 == 0（全部消除）。
"""
import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.compliance.rule_engine import evaluate as _rule_evaluate  # noqa: E402
from src.pipeline import rank_primary, select_conclusion_segments  # noqa: E402

logging.disable(logging.NOTSET)


def _seg(source, license_, level, sim, sid=1, start=1, end=5):
    return {
        "id": sid,
        "lines": f"{start}-{end}",
        "line_start": start,
        "line_end": end,
        "source": source,
        "license": license_,
        "score": sim,
        "verification_level": level,
    }


# ---------- select_conclusion_segments 单元测试 ----------

def test_conclusion_strong_segments_drive():
    """L1/L2 强段参与结论；非主证据的 L3 弱段不参与。"""
    segs = rank_primary(
        [_seg("real-a", "MIT", 2, 0.95, 1), _seg("gpl-shadow", "GPL-3.0", 3, 0.12, 2)]
    )
    concl = select_conclusion_segments(segs)
    assert {s["id"] for s in concl} == {1}
    assert segs[0]["drives_conclusion"] is True
    assert segs[1]["drives_conclusion"] is False


def test_conclusion_primary_always_included():
    """主证据段（即使 L3）始终参与结论——删/重排查询的正确源不被排除。"""
    segs = rank_primary(
        [
            _seg("correct-l3", "MIT", 3, 0.84, 3),
            _seg("spurious-l2-a", "MIT", 2, 0.12, 1),
            _seg("spurious-l2-b", "MIT", 2, 0.10, 2),
        ]
    )
    concl = select_conclusion_segments(segs)
    ids = {s["id"] for s in concl}
    assert 3 in ids  # 主证据（correct-l3, L3）被纳入
    assert {1, 2} <= ids  # 强段 L2 全部纳入
    assert all(s["drives_conclusion"] for s in concl)


def test_conclusion_l3_only_single_segment():
    segs = rank_primary([_seg("only-l3", "MIT", 3, 0.70, 1)])
    concl = select_conclusion_segments(segs)
    assert {s["id"] for s in concl} == {1}


def test_conclusion_empty():
    assert select_conclusion_segments([]) == []


def test_conclusion_weak_l4_excluded():
    """L4（redup 行级）非主证据段同样不参与结论。"""
    segs = rank_primary(
        [_seg("real-a", "MIT", 2, 0.90, 1), _seg("lgpl-shadow", "LGPL-3.0", 4, 0.15, 2)]
    )
    concl = select_conclusion_segments(segs)
    assert {s["id"] for s in concl} == {1}
    assert segs[1]["drives_conclusion"] is False


# ---------- 机制端到端：弱 GPL 段被排除 → 误报消除 ----------

def test_mechanism_weak_gpl_escalation_eliminated():
    """同组段：旧聚合（全段参与）→ INCOMPATIBLE（误报）；新聚合（主证据驱动）
    → COMPATIBLE（正确）。这是混合基准误报下降的机制本体。"""
    segs = rank_primary(
        [
            _seg("real-a", "MIT", 2, 0.95, 1),
            _seg("gpl-shadow", "GPL-3.0", 3, 0.12, 2),  # 弱 L3 伪匹配
        ]
    )
    status_old = _rule_evaluate(list(segs), "MIT")["status"]
    status_new = _rule_evaluate(select_conclusion_segments(segs), "MIT")["status"]
    assert status_old == "INCOMPATIBLE"  # 基线误报
    assert status_new == "COMPATIBLE"  # 主证据驱动消除误报


def test_mechanism_unknown_weak_escalation_eliminated():
    """弱 UNKNOWN 许可证段：旧聚合 NEEDS_REVIEW，新聚合 COMPATIBLE。"""
    segs = rank_primary(
        [
            _seg("real-a", "MIT", 2, 0.95, 1),
            _seg("unknown-shadow", "UNKNOWN", 3, 0.12, 2),
        ]
    )
    status_old = _rule_evaluate(list(segs), "MIT")["status"]
    status_new = _rule_evaluate(select_conclusion_segments(segs), "MIT")["status"]
    assert status_old == "NEEDS_REVIEW"
    assert status_new == "COMPATIBLE"


# ---------- 混合许可证基准（全量，约 6 分钟） ----------

@pytest.fixture(scope="module")
def mixed_results():
    import evaluation.benchmark_mixed as _bm

    _bm.main()
    p = ROOT / "data" / "benchmark_mixed" / "results.json"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.mark.slow
def test_mixed_benchmark_false_escalation_eliminated(mixed_results):
    """混合 KB 上旧聚合存在合规误报（>0），新聚合全部消除（==0）。"""
    s = mixed_results["summary"]
    assert s["old_aggregation_wrong"] > 0, "干扰实体未产生弱匹配，误报基线缺失"
    assert s["new_aggregation_wrong"] == 0, "主证据驱动后仍有合规误报"
    assert s["eliminated_false_escalations"] == s["old_aggregation_wrong"]
    assert s["n_positive"] > 0


@pytest.mark.slow
def test_mixed_benchmark_attribution_and_negatives(mixed_results):
    """混合 KB 下归属准确率 1.0；负样本零误报（新聚合）。"""
    s = mixed_results["summary"]
    assert s["attribution_accuracy"] == pytest.approx(1.0)
    for r in mixed_results["rows"]:
        if r["kind"] == "negative":
            assert r["status_new"] == "COMPATIBLE", f"负样本 {r['id']} 被误判"
            assert r["new_wrong"] is False


@pytest.mark.slow
def test_mixed_benchmark_escalation_cases_sources(mixed_results):
    """被消除的误报：**至少一个**非兼容许可证弱段（肇事），且肇事弱段来源均为
    干扰项目（GPL/MPL/LGPL 真实包）；其余弱段为兼容真实包（不构成肇事）。

    真实干扰实体较多时，一个查询可与多个干扰实体共享锚点（多个肇事弱段并存）
    ——较 v4 合成干扰（每例恰一个肇事段）更贴近真实跨项目近邻分布。
    """
    cases = json.loads(
        (ROOT / "data" / "benchmark_mixed" / "escalation_cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(cases) > 0
    distractor_srcs = {"distractor-gpl", "distractor-mpl", "distractor-lgpl"}
    for c in cases:
        weak = c["excluded_weak"]
        bad = [s for s in weak if s.get("license") in ("GPL-2.0", "MPL-2.0", "LGPL-3.0")]
        assert len(bad) >= 1, f"{c['id']} 无肇事弱段"
        assert all(s["source"] in distractor_srcs for s in bad), (
            f"{c['id']} 肇事弱段含非干扰项目: {[s['source'] for s in bad]}"
        )
