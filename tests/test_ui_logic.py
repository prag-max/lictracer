# -*- coding: utf-8 -*-
"""桌面端纯逻辑层单元测试：扫描器 / 筛选 / 项目级聚合（不启动 Qt 事件循环）。"""
from src.ui.scanner import DEFAULT_EXCLUDE_DIRS, filter_by_text, scan_python_files
from src.ui.summary import aggregate_project


def _mk(tmp_path, rel):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x = 1\n", encoding="utf-8")
    return p


def test_scan_excludes_and_sorts(tmp_path):
    _mk(tmp_path, "a.py")
    _mk(tmp_path, "sub/b.py")
    _mk(tmp_path, "__pycache__/junk.py")
    _mk(tmp_path, ".venv/lib/x.py")
    _mk(tmp_path, "notes.txt")
    found = scan_python_files(tmp_path)
    assert [p.name for p in found] == ["a.py", "b.py"]  # 排除隐藏/缓存目录，仅 .py，稳定排序
    assert all(p.is_absolute() for p in found)


def test_scan_custom_suffix_and_exclude(tmp_path):
    _mk(tmp_path, "a.py")
    _mk(tmp_path, "b.js")
    assert scan_python_files(tmp_path, suffix=".js")[0].name == "b.js"
    only_a = scan_python_files(tmp_path, exclude_dirs=DEFAULT_EXCLUDE_DIRS | {"sub"})
    _mk(tmp_path, "sub/c.py")
    assert [p.name for p in scan_python_files(tmp_path, exclude_dirs={"sub"})] == ["a.py"]
    assert only_a[0].name == "a.py"


def test_scan_nonexistent_returns_empty(tmp_path):
    assert scan_python_files(tmp_path / "nope") == []


def test_filter_by_text():
    paths = ["E:/proj/tests/util.py", "E:/proj/main_v2.py", "E:/proj/main.py"]
    assert filter_by_text(paths, "tests") == [paths[0]]
    assert len(filter_by_text(paths, "main")) == 2
    assert filter_by_text(paths, "") == paths
    assert filter_by_text(paths, "  ") == paths


def _entry(path, status="COMPATIBLE", n_segments=0, ambiguous=False):
    report = {
        "summary": {"conclusion": status, "risk_level": "LOW"},
        "compliance_result": {"status": status},
        "segments": [{"id": i} for i in range(n_segments)],
        "attribution": {"attribution_ambiguous": ambiguous},
        "methodology": {"tree_sitter": "available", "retriever_mode": "full", "kb_files": 5},
    }
    return {"path": path, "report": report, "error": ""}


def test_aggregate_worst_status_wins_and_counts():
    entries = [
        _entry("a.py", "COMPATIBLE"),
        _entry("b.py", "NEEDS_REVIEW", n_segments=2),
        _entry("c.py", "INCOMPATIBLE", n_segments=1),
        _entry("d.py", "COMPATIBLE"),
    ]
    agg = aggregate_project(entries)
    assert agg["status"] == "INCOMPATIBLE"
    assert agg["risk_level"] == "HIGH"
    assert agg["counts"]["INCOMPATIBLE"] == 1
    assert agg["counts"]["COMPATIBLE"] == 2
    assert agg["hit_files"] == 2  # b/c 有片段
    assert agg["analyzed"] == 4 and agg["total"] == 4


def test_aggregate_errors_isolated_not_silent_compat():
    entries = [_entry("ok.py", "COMPATIBLE"), {"path": "bad.py", "report": None, "error": "ValueError: x"}]
    agg = aggregate_project(entries)
    assert agg["analyzed"] == 1 and agg["errors"][0]["path"] == "bad.py"
    assert agg["status"] == "COMPATIBLE"  # 成功文件仍正常聚合

    agg_all_err = aggregate_project([{"path": "x.py", "report": None, "error": "boom"}])
    assert agg_all_err["status"] == "UNKNOWN"  # 全失败不得伪装成兼容


def test_aggregate_collects_ambiguous_files():
    entries = [
        _entry("amb.py", "NEEDS_REVIEW", ambiguous=True),
        _entry("clear.py", "COMPATIBLE"),
    ]
    agg = aggregate_project(entries)
    assert agg["ambiguous"] == ["amb.py"]
