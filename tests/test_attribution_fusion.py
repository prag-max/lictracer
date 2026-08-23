# -*- coding: utf-8 -*-
"""主证据融合（次优证据融合）单元测试：布尔判定门控 × 相似度排序联合决策。

覆盖：
- ``rank_primary``：已验证段按 (similarity 最高, verification_level 最小, source)
  排序并标记 is_primary（相似度主导：弱结构伪匹配的相似度远低于正确来源，
  仅按布尔级会把伪匹配误判为主证据）；
- ``attribution_of``：主证据源 + 归属歧义标记（不同来源 (level, sim) 完全并列 →
  歧义，同源多段不计歧义；精确相等判定，无阈值）；
- 端到端：聚合（异源不合并）→ 排序 → 归属。
"""

from src.aggregator.segment_aggregator import aggregate
from src.pipeline import attribution_of, rank_primary


def _seg(source, level, sim, start=1, end=5):
    return {
        "id": start,
        "lines": f"{start}-{end}",
        "line_start": start,
        "line_end": end,
        "source": source,
        "license": "MIT",
        "score": sim,
        "verification_level": level,
    }


def test_rank_primary_orders_by_similarity_then_level():
    segs = rank_primary(
        [
            _seg("weak_l3_hi_sim", 3, 0.95),
            _seg("mid_l2", 2, 0.60),
            _seg("strong_l1", 1, 0.50),
            _seg("l2_hi_sim", 2, 0.90),
        ]
    )
    # 相似度主导：0.95(L3) > 0.90(L2) > 0.60(L2) > 0.50(L1)
    assert [s["source"] for s in segs] == [
        "weak_l3_hi_sim", "l2_hi_sim", "mid_l2", "strong_l1",
    ]
    assert [s["is_primary"] for s in segs] == [True, False, False, False]


def test_attribution_primary_source():
    # 高相似度弱级（L3, 0.9）不应压过低相似度强级（L2, 0.7）——真实伪匹配相似度很低，
    # 此处 0.9>0.7 故 B 为主证据（相似度主导的语义）
    segs = rank_primary([_seg("A", 2, 0.7), _seg("B", 3, 0.9)])
    a = attribution_of(segs)
    assert a["primary_source"] == "B"
    assert a["attribution_ambiguous"] is False


def test_attribution_weak_pseudo_match_not_primary():
    """真实场景：正确来源 L1 高相似度 vs 弱伪匹配 L2 低相似度 → 正确来源主证据。"""
    segs = rank_primary([_seg("correct", 1, 0.95), _seg("pseudo", 2, 0.12)])
    a = attribution_of(segs)
    assert a["primary_source"] == "correct"
    assert a["attribution_ambiguous"] is False


def test_attribution_ambiguous_on_exact_tie_different_source():
    segs = rank_primary([_seg("A", 2, 0.70), _seg("B", 2, 0.70)])
    a = attribution_of(segs)
    assert a["primary_source"] == "A"  # 同 (sim, level) 时按 source 字典序取主证据
    assert a["attribution_ambiguous"] is True


def test_attribution_not_ambiguous_for_same_source_duplicates():
    # 同一来源多个行区间段（同 KB 文件多处命中）不构成归属歧义
    segs = rank_primary([_seg("A", 2, 0.70), _seg("A", 2, 0.70, start=10, end=20)])
    a = attribution_of(segs)
    assert a["primary_source"] == "A"
    assert a["attribution_ambiguous"] is False


def test_attribution_empty():
    assert attribution_of([]) == {"primary_source": None, "attribution_ambiguous": False}


def test_fusion_chain_aggregate_rank_attribution():
    """端到端：跨源证据 → 聚合（异源不合并）→ 主证据排序 → 归属。
    正确来源 A(L1, sim 0.95) + 弱伪匹配 B(L3, sim 0.12) → 两个独立段，
    主证据源 A，无歧义。"""
    evidence = [
        {"line_start": 1, "line_end": 5, "similarity": 0.95, "project": "A",
         "license": "MIT", "verification_level": 1},
        {"line_start": 3, "line_end": 8, "similarity": 0.12, "project": "B",
         "license": "MIT", "verification_level": 3},
    ]
    segs = rank_primary(aggregate(evidence))
    a = attribution_of(segs)
    assert len(segs) == 2  # 异源不合并
    assert segs[0]["source"] == "A"
    assert segs[0]["is_primary"] is True
    assert a["primary_source"] == "A"
    assert a["attribution_ambiguous"] is False
