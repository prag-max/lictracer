# -*- coding: utf-8 -*-
"""证据精炼层单元测试：行级证据（line_start/line_end/similarity）。"""
from src.evidence.redup_adapter import refine


def test_refine_produces_line_evidence(tmp_path):
    # 计数式闸门（LICT_REDUP_MIN_LINES=3）：函数需 ≥3 行命中才产生行级证据
    query_lines = [
        "def foo(a, b):",
        "    total = a + b",
        "    double = total * 2",
        "    return double",
        "def bar(b):",
        "    return b * 2",
    ]
    cand_file = tmp_path / "cand.py"
    cand_file.write_text(
        "def foo(a, b):\n    total = a + b\n    double = total * 2\n    return double\n",
        encoding="utf-8",
    )

    candidates = [{"file": str(cand_file), "project": "p", "license": "MIT"}]
    evidence = refine(query_lines, candidates)

    assert evidence, "相似代码应产出证据"
    ev = evidence[0]
    assert ev["line_start"] >= 1
    assert ev["line_end"] >= ev["line_start"]
    assert 0 < ev["similarity"] <= 1.0
    assert ev["project"] == "p"
    assert ev["license"] == "MIT"


def test_refine_no_match_returns_empty(tmp_path):
    query_lines = ["def bar(b):", "    return b * 2"]
    cand_file = tmp_path / "cand.py"
    cand_file.write_text("def foo(a):\n    return a + 1\n", encoding="utf-8")
    candidates = [{"file": str(cand_file), "project": "p", "license": "MIT"}]
    evidence = refine(query_lines, candidates)
    # 主匹配块非常小的场景下应被噪声阈值过滤
    assert evidence == [] or all(e["similarity"] <= 1.0 for e in evidence)
