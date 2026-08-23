# -*- coding: utf-8 -*-
"""端到端冒烟测试（不依赖第三方库，离线可跑）。

构造两份相似代码 + 一个 GPL 片段，直接走 pipeline 核心链，
断言能产出 INCOMPATIBLE 结论。
"""
import json

from src.pipeline import analyze_file


def _build_kb(tmp_path):
    kb = tmp_path / "kb"
    (kb / "projects" / "mitlib").mkdir(parents=True)
    (kb / "projects" / "gpllib").mkdir(parents=True)
    (kb / "licenses.json").write_text(
        json.dumps({"mitlib": "MIT", "gpllib": "GPL-3.0"}), encoding="utf-8"
    )
    (kb / "projects" / "mitlib" / "util.py").write_text(
        "def send_request(url):\n    return urllib.request.urlopen(url).read()\n",
        encoding="utf-8",
    )
    (kb / "projects" / "gpllib" / "finance.py").write_text(
        "def calculate_interest(principal, rate, time):\n    return principal * (1 + rate) ** time\n",
        encoding="utf-8",
    )
    return kb


def test_end_to_end_two_sources_incompatible(tmp_path):
    kb = _build_kb(tmp_path)
    inp = tmp_path / "in.py"
    inp.write_text(
        "def send_request(url):\n"
        "    return urllib.request.urlopen(url).read()\n"
        "\n"
        "\n"
        "def calculate_interest(principal, rate, time):\n"
        "    return principal * (1 + rate) ** time\n",
        encoding="utf-8",
    )

    report = analyze_file(
        str(inp), kb_path=kb, project_license="MIT", include_summary=False
    )

    assert report["summary"]["conclusion"] == "INCOMPATIBLE"
    assert report["summary"]["total_segments"] >= 2
    licenses = {s["license"] for s in report["segments"]}
    assert "MIT" in licenses
    assert "GPL-3.0" in licenses


def test_builtin_sample_end_to_end():
    """直接跑内置 sample.py（requests/MIT + finance-lib/GPL-3.0）。"""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    report = analyze_file(str(root / "sample.py"), include_summary=False)

    assert report["summary"]["conclusion"] == "INCOMPATIBLE"
    assert report["summary"]["total_segments"] >= 2
    licenses = {s["license"] for s in report["segments"]}
    assert "MIT" in licenses
    assert "GPL-3.0" in licenses
