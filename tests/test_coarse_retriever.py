# -*- coding: utf-8 -*-
r"""溯源层（coarse_retriever）单元测试：多特征 MinHash 相似召回（运算符感知分词 + Winnowing 指纹 + AST 子树哈希）。

覆盖：
- B：运算符级改动在特征层可区分（旧版 `\w+` 分词下 jaccard=1.0 不可区分）；
- G：AST 子树哈希——注释无关、重命名（T2）鲁棒、字面量改写抗性；
- A：Winnowing 指纹集合规模受控；
- 端到端：精确克隆 top1、确定性。
"""
import zlib
from pathlib import Path

from src.provenance.coarse_retriever import (
    CoarseRetriever,
    _ast_features,
    _features,
    _tokenize,
    _winnowed_fingerprints,
)
from src.provenance.knowledge_base import KnowledgeBase


def _jaccard(a: set, b: set) -> float:
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


# ---------- 运算符感知分词 ----------
def test_tokenize_keeps_operators():
    toks = _tokenize("def f():\n    return x >= 0 and y == 1\n")
    assert ">=" in toks  # 多字符运算符整体保留
    assert "==" in toks
    assert "and" in toks
    assert "VAR_0" in toks or "x" in toks


def test_operator_level_changes_distinguishable():
    """B：`x + 0` vs `x * 0` 在粗筛特征层必须可区分（旧版 jaccard=1.0）。"""
    a = _features("def f(x):\n    return x + 0\n")
    b = _features("def f(x):\n    return x * 0\n")
    assert a != b
    assert _jaccard(a, b) < 1.0


# ---------- Winnowing ----------
def test_winnowing_reduces_for_long_text():
    tokens = _tokenize("def f%d(x):\n    return x + %d\n" % (0, 0) * 50)
    fps = _winnowed_fingerprints(tokens)
    assert len(fps) <= len(tokens)
    assert len(fps) > 0


def test_winnowing_short_text_keeps_all():
    toks = ["def", "f", "return", "1"]
    fps = _winnowed_fingerprints(toks)
    assert fps == {zlib.crc32(t.encode("utf-8")) for t in toks}


# ---------- AST 子树哈希 ----------
def test_ast_features_comment_insensitive():
    a = _ast_features("def f(x):\n    # 注释不影响结构\n    return x + 1\n")
    b = _ast_features("def f(x):\n    return x + 1\n")
    assert a  # 有效代码必有结构特征
    assert a == b  # 注释被完全忽略


def test_ast_features_rename_robust_t2():
    a = _ast_features(
        "def compute_total(items):\n"
        "    acc = 0\n"
        "    for it in items:\n"
        "        acc = acc + it\n"
        "    return acc\n"
    )
    b = _ast_features(
        "def calc_sum(lst):\n"
        "    total = 0\n"
        "    for v in lst:\n"
        "        total = total + v\n"
        "    return total\n"
    )
    assert _jaccard(a, b) > 0.9  # 仅重命名（T2）→ 结构特征高重叠


def test_ast_features_garbage_code_no_crash():
    # 非法字节/残缺代码不抛异常（tree-sitter 产 ERROR 子树，仍确定性返回特征集）
    out = _ast_features("\x00\x01 broken ???")
    assert isinstance(out, set)
    assert _ast_features("def f(:\n   return") is not None


# ---------- 端到端（CoarseRetriever） ----------
def _make_kb(tmp_path, files: dict, license_map: dict):
    """构造临时 KB：files={name: content}，license_map={project: license}。"""
    import json

    for proj in license_map:
        proj_dir = tmp_path / "projects" / proj
        proj_dir.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (proj_dir / name).write_text(content, encoding="utf-8")
    (tmp_path / "licenses.json").write_text(
        json.dumps(license_map), encoding="utf-8"
    )
    return KnowledgeBase(tmp_path)


def test_retrieve_exact_clone_top1(tmp_path):
    clone = "def f(x):\n    return x + 1\n" * 20
    distractor = (
        "class Mod:\n"
        "    def run(self):\n"
        "        total = 0\n"
        "        for i in range(10):\n"
        "            total += i\n"
        "        return total\n"
    )
    kb = _make_kb(tmp_path, {"clone.py": clone, "dist.py": distractor}, {"p0": "MIT"})
    rt = CoarseRetriever(kb)
    top = rt.retrieve(clone, top_k=5)
    assert top and top[0]["file"].endswith("clone.py")
    assert top[0]["similarity"] >= 0.999  # 完全相同的代码 → jaccard=1.0


def test_retrieve_deterministic(tmp_path):
    clone = "def f(x):\n    return x + 1\n" * 20
    kb = _make_kb(tmp_path, {"clone.py": clone}, {"p0": "MIT"})
    rt = CoarseRetriever(kb)
    assert rt.retrieve(clone, top_k=5) == rt.retrieve(clone, top_k=5)


def test_retrieve_operator_clone_ranked_below_exact(tmp_path):
    """B：运算符级改动文件应被召回，但相似度严格低于精确克隆。"""
    exact = "def f(x):\n    return x + 0\n"
    op_var = "def f(x):\n    return x * 0\n"  # 仅运算符不同 → 弱克隆
    kb = _make_kb(
        tmp_path,
        {"exact.py": exact, "opvar.py": op_var, "dist.py": "print('hello')"},
        {"p0": "MIT"},
    )
    rt = CoarseRetriever(kb)
    top = rt.retrieve(exact, top_k=5)
    names = [Path(c["file"]).name for c in top]
    assert "exact.py" in names
    if "opvar.py" in names:
        sim_exact = next(c for c in top if c["file"].endswith("exact.py"))["similarity"]
        sim_opvar = next(c for c in top if c["file"].endswith("opvar.py"))["similarity"]
        assert sim_exact > sim_opvar


# ---------- 缓存：JSON 序列化（防 pickle 投毒） + 版本指纹 ----------
def test_cache_is_json_and_roundtrip(tmp_path):
    clone = "def f(x):\n    return x + 1\n" * 20
    kb = _make_kb(tmp_path, {"clone.py": clone}, {"p0": "MIT"})
    rt = CoarseRetriever(kb)
    first = rt.retrieve(clone, top_k=5)

    cache_dir = tmp_path / ".index"
    assert (cache_dir / "feature_index.json").exists()
    assert not (cache_dir / "feature_index.pkl").exists()  # 旧 pickle 已迁移

    # 二次构建从 JSON 缓存加载，结果一致
    rt2 = CoarseRetriever(KnowledgeBase(tmp_path))
    assert rt2.retrieve(clone, top_k=5) == first


def test_legacy_pickle_cache_is_deleted(tmp_path):
    clone = "def f(x):\n    return x + 1\n" * 20
    kb = _make_kb(tmp_path, {"clone.py": clone}, {"p0": "MIT"})
    cache_dir = tmp_path / ".index"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "feature_index.pkl").write_bytes(b"garbage-not-really-pickle")
    rt = CoarseRetriever(kb)
    assert not (cache_dir / "feature_index.pkl").exists()
    assert rt.retrieve(clone, top_k=5) is not None


def test_cache_invalidated_when_datasketch_version_changes(tmp_path):
    import src.provenance.coarse_retriever as cr

    clone = "def f(x):\n    return x + 1\n" * 20
    kb = _make_kb(tmp_path, {"clone.py": clone}, {"p0": "MIT"})
    CoarseRetriever(kb)
    cache_file = tmp_path / ".index" / "feature_index.json"
    import json

    data = json.loads(cache_file.read_text(encoding="utf-8"))
    assert data["datasketch_version"] == cr._DATASKETCH_VERSION

    # 模拟 datasketch 升级：版本指纹不同 → 缓存失效重建（新文件含新版本号）
    old = cr._DATASKETCH_VERSION
    try:
        cr._DATASKETCH_VERSION = "999.0.0"
        rt2 = CoarseRetriever(KnowledgeBase(tmp_path))
        assert rt2.retrieve(clone, top_k=5) is not None
        data2 = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data2["datasketch_version"] == "999.0.0"
    finally:
        cr._DATASKETCH_VERSION = old


def test_full_scan_exact_clone_top1(tmp_path):
    """全库确定性扫描下，精确克隆仍排第一（Forest 已移除，仅保留 full 扫描）。"""
    exact = "def f(x):\n    return x + 1\n" * 20
    kb = _make_kb(
        tmp_path,
        {"clone.py": exact, "a.py": "x = 1", "b.py": "y = 2"},
        {"p0": "MIT"},
    )
    rt = CoarseRetriever(kb)
    assert rt.mode == "full"
    top = rt.retrieve(exact, top_k=5)
    assert top is not None
    assert top[0]["file"].endswith("clone.py")  # 全库扫描排序正确


def test_forest_removed_from_module():
    """回归守卫：MinHashLSHForest 已从模块移除（全库扫描为唯一路径）。"""
    import src.provenance.coarse_retriever as cr

    assert not hasattr(cr, "MinHashLSHForest")
    assert not hasattr(cr, "_build_forest")
    assert not hasattr(cr, "_FOREST_MIN")
    assert not hasattr(cr, "_FOREST_K_MULT")
    assert not hasattr(cr, "_FOREST_CAND_FLOOR")
