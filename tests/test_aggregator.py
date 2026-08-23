# -*- coding: utf-8 -*-
"""多源聚合层单元测试：混剪拆分 + 重叠合并规则。"""
from src.aggregator.segment_aggregator import aggregate


def test_split_two_distinct_sources():
    evidence = [
        {"line_start": 2, "line_end": 3, "similarity": 0.90, "project": "A", "license": "MIT"},
        {"line_start": 6, "line_end": 7, "similarity": 0.85, "project": "B", "license": "GPL-3.0"},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 2
    assert segments[0]["source"] == "A"
    assert segments[1]["source"] == "B"
    assert segments[0]["id"] == 1
    assert segments[1]["id"] == 2
    assert segments[0]["license"] == "MIT"
    assert segments[1]["license"] == "GPL-3.0"


def test_merge_overlap_keeps_highest_similarity():
    evidence = [
        {"line_start": 1, "line_end": 5, "similarity": 0.80, "project": "A", "license": "MIT"},
        {"line_start": 3, "line_end": 8, "similarity": 0.95, "project": "A", "license": "MIT"},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 1
    assert segments[0]["line_start"] == 1
    assert segments[0]["line_end"] == 8
    assert segments[0]["score"] == 0.95


def test_gap_between_different_sources_splits():
    evidence = [
        {"line_start": 1, "line_end": 2, "similarity": 0.90, "project": "A", "license": "MIT"},
        {"line_start": 6, "line_end": 7, "similarity": 0.90, "project": "B", "license": "GPL-3.0"},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 2


def test_empty_evidence():
    assert aggregate([]) == []


def test_merge_cross_source_overlap_splits_into_two_segments():
    """跨源重叠证据永不合并：每段单一来源、归属一致。
    A(L1, sim 0.5) 与 B(L3, sim 0.9) 重叠 → 两个独立段，source/level 各自一致。"""
    evidence = [
        {"line_start": 1, "line_end": 5, "similarity": 0.50, "project": "A",
         "license": "MIT", "verification_level": 1},
        {"line_start": 3, "line_end": 8, "similarity": 0.90, "project": "B",
         "license": "GPL-3.0", "verification_level": 3},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 2
    by_src = {s["source"]: s for s in segments}
    assert by_src["A"]["verification_level"] == 1
    assert by_src["A"]["license"] == "MIT"
    assert by_src["B"]["verification_level"] == 3
    assert by_src["B"]["license"] == "GPL-3.0"


def test_merge_same_source_takes_best_level_and_sim():
    """同源合并：level 取最强（min），score 取最高（max）——同一来源证据融合。"""
    evidence = [
        {"line_start": 1, "line_end": 5, "similarity": 0.50, "project": "A",
         "license": "MIT", "verification_level": 1},
        {"line_start": 3, "line_end": 8, "similarity": 0.90, "project": "A",
         "license": "MIT", "verification_level": 3},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 1
    assert segments[0]["source"] == "A"
    assert segments[0]["verification_level"] == 1
    assert segments[0]["score"] == 0.9


def test_adjacent_different_sources_split():
    """相邻（gap=1）异源证据也各自成段：不同来源即使相邻也不吸收合并。"""
    evidence = [
        {"line_start": 1, "line_end": 2, "similarity": 0.60, "project": "A",
         "license": "MIT", "verification_level": 2},
        {"line_start": 3, "line_end": 8, "similarity": 0.95, "project": "B",
         "license": "Apache-2.0", "verification_level": 2},
    ]
    segments = aggregate(evidence)
    assert len(segments) == 2
    assert {s["source"] for s in segments} == {"A", "B"}
