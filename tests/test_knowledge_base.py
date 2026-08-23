# -*- coding: utf-8 -*-
"""知识库管理单元测试：licenses.json 校验与未映射告警。"""
import json

from src.provenance.knowledge_base import KnowledgeBase


def _write_kb(tmp_path, license_map=None, top_level_invalid=False):
    if top_level_invalid:
        (tmp_path / "licenses.json").write_text("[1,2,3]", encoding="utf-8")
    elif license_map is not None:
        (tmp_path / "licenses.json").write_text(
            json.dumps(license_map), encoding="utf-8"
        )
    (tmp_path / "projects" / "alpha").mkdir(parents=True)
    (tmp_path / "projects" / "alpha" / "a.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "projects" / "beta").mkdir(parents=True)
    (tmp_path / "projects" / "beta" / "b.py").write_text("y = 2", encoding="utf-8")
    return KnowledgeBase(tmp_path)


def test_normal_license_map(tmp_path):
    kb = _write_kb(tmp_path, {"alpha": "MIT", "beta": "Apache-2.0"})
    assert kb.get_license("alpha") == "MIT"
    files = {f["project"]: f["license"] for f in kb.list_files()}
    assert files == {"alpha": "MIT", "beta": "Apache-2.0"}


def test_missing_project_license_is_unknown(tmp_path):
    # beta 未映射 → UNKNOWN
    kb = _write_kb(tmp_path, {"alpha": "MIT"})
    files = {f["project"]: f["license"] for f in kb.list_files()}
    assert files["beta"] == "UNKNOWN"


def test_empty_license_value_is_unknown(tmp_path):
    kb = _write_kb(tmp_path, {"alpha": "  ", "beta": "Apache-2.0"})
    assert kb.get_license("alpha") == "UNKNOWN"
    assert kb.get_license("beta") == "Apache-2.0"


def test_invalid_top_level_is_ignored(tmp_path):
    kb = _write_kb(tmp_path, top_level_invalid=True)
    assert kb.licenses == {}
    assert all(f["license"] == "UNKNOWN" for f in kb.list_files())
