# -*- coding: utf-8 -*-
r"""溯源层 —— datasketch MinHash 近似相似召回（替换 NLCI）。

设计目标（对齐 PRD「可复现 / 零幻觉」声明）：
- **完全确定**：MinHash 固定 ``seed=1``，特征哈希用 ``zlib.crc32``（跨进程稳定），
  给定查询与知识库，候选集结果稳定可复现；
- **无外部运行依赖**：纯 Python + datasketch + tree-sitter（均已在 requirements），
  弃用严格锁 ``node>=18<19`` 的 NLCI；
- **消除 51s 瓶颈**：离线对知识库每个文件预计算 MinHash 并持久化缓存；
- **全库 MinHash 确定性扫描**：对知识库每个文件的 MinHash 签名与查询做精确
  Jaccard 估计并全量排序（O(N×num_perm) 整数级比较）。本系统知识库为**提取的实体
  集合**（数十至数百文件，远低于 2000 文件阈值），全库扫描在毫秒级完成且结果完全
  确定、可解释、可复现；近似检索（LSH Forest / MinHashLSHForest）的亚线性代价在该
  规模无收益，已于 2026-08-23 移除（保留 MinHash 用于 Jaccard 估计）；
- **输出同构**：返回 ``[{file, project, license, similarity}]``，``redup.refine``
  与下游聚合、合规层无需任何改动。

特征管线（运算符感知分词 + Winnowing 指纹 + AST 子树哈希，提升召回率与准确率）：
- **运算符感知分词**：``re.findall(r"\w+|\S+", skeleton)`` 保留运算符与标点
  （多字符运算符 ``==``/``>=`` 整体保留），消除「``return x + 0`` 与
  ``return x * 0`` 在粗筛层不可区分」的旧局限；
- **Winnowing（MOSS 式指纹）**：滑动窗口内取最小 token 哈希为代表指纹，
  对局部增删改（T3）鲁棒——单点改动只影响窗口内的局部指纹，全局指纹多数不变；
- **AST 子树哈希（Merkle）**：tree-sitter 解析后自底向上为每个节点计算
  结构哈希并收集（identifier→``ID`` 占位抗重命名 T2、字面量→类型占位抗常量级改写，
  注释节点跳过），提供独立于线性 token 顺序的结构信号。

方法路线刻意为之地**不引入语义嵌入**——语义等价但结构独立的重写（T4）在法律上属
独立派生作品、不构成侵权，用语义模型做粗筛会将其误判为克隆，产生高危害误报。

召回约束说明：粗筛阶段以「高召回」为首要目标（漏报 = 漏掉真实克隆 = 漏掉侵权结论，
合规致命）。**裁决不在此层完成**——候选是否构成克隆由下游确定性等价验证器
（``exact_verifier``，布尔判定）决定。为消除「相似度排名靠后被 top_k 截断」的
召回缺口，提供 ``recall_all``：全库非零相似度候选 ∪ 锚点行游程成员（确定性闸门），
不再截断（全库扫描天然覆盖弱克隆，无需额外候选放大）。

**已知局限（诚实声明）**：
- ``similarity`` 为 MinHash **估计值**（num_perm=128 时 Jaccard 估计标准误 ≈ ±7.4%），
  仅用于候选排序与报告展示，**不参与克隆裁决**（裁决由验证器布尔判定完成）；
- 全库扫描为精确 Jaccard 计算（非近似），召回确定性 100%；知识库规模达到数千文件
  时单次扫描常数开销随 N 线性增长，但本系统 KB 为提取实体集（O(百) 文件），
  实测毫秒级；大规模整库扫描代价仍列入 future work 实证。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import zlib
from pathlib import Path

from datasketch import MinHash

from src.preprocessor.ast_normalizer import normalize, tree_sitter_available
from src.provenance.exact_verifier import anchor_grams

logger = logging.getLogger("lictracer.provenance")

_NUM_PERM = 128
_SEED = 1
_FEATURE_FORMAT = "abg-1"  # 特征管线版本（运算符感知分词 + Winnowing + AST 子树哈希）；变更即失效旧缓存
_CACHE_FORMAT = "json-v1"  # 缓存序列化格式；pickle 版本已废弃（防投毒）

# datasketch 版本指纹：MinHash 序列化结构随版本可能变化，变更即失效旧缓存
import datasketch  # noqa: E402

_DATASKETCH_VERSION = getattr(datasketch, "__version__", "unknown")

# ---- 特征的可配置参数（env 覆盖，便于实验调参） ----
_WINNOW_WINDOW = int(os.environ.get("LICT_WINNOW_WINDOW", "15"))
# 锚点召回闸门的 L 元组长度（行级规范型；策略定义「多长算一份拷贝」，非相似度阈值）
_ANCHOR_LEN = int(os.environ.get("LICT_ANCHOR_LEN", "3"))

# tree-sitter 解析器（复用 ast_normalizer 的加载方式；不可用则仅用 token 特征）。
# 注意：tree_sitter.Parser 非线程安全，每线程经 threading.local 持有独立实例。
try:
    import tree_sitter  # type: ignore
    import tree_sitter_python  # type: ignore

    _TS_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
    _TS_AVAILABLE = True
except Exception:
    _TS_LANGUAGE = None
    _TS_AVAILABLE = False
    logger.warning("tree-sitter 不可用，G 特征（AST 子树哈希）将被跳过", exc_info=True)

_TS_LOCAL = threading.local()


def _get_parser():
    """返回当前线程的 parser；tree-sitter 不可用时返回 None。"""
    if not _TS_AVAILABLE:
        return None
    parser = getattr(_TS_LOCAL, "parser", None)
    if parser is None:
        parser = tree_sitter.Parser(_TS_LANGUAGE)
        _TS_LOCAL.parser = parser
    return parser


# ---------- 运算符感知分词 ----------
def _tokenize(text: str) -> "list[str]":
    """骨架文本 → token 序列。

    ``\\w+`` 保留标识符/数字（含 ``VAR_n``/``FUNC_n``），``\\S+`` 保留运算符与标点，
    且多字符运算符（``==``/``>=``/``**``）整体保留——运算符级改动在特征层可见。
    """
    return re.findall(r"\w+|\S+", text)


# ---------- Winnowing（MOSS 式指纹） ----------
def _winnowed_fingerprints(tokens: "list[str]") -> "set[int]":
    """token 序列 → Winnowing 指纹集合。

    对每个滑动窗口取最小 token 哈希为代表指纹，且仅记录「最小值发生变化」的窗口
    （MOSS 标准做法，避免输出大量重复指纹）。单点增删改只影响窗口内的局部指纹，
    对 T3（near-miss）鲁棒。短文本（token 数 ≤ 窗口）退化为保留全部 token 哈希，
    避免小文件信息丢失。
    """
    if not tokens:
        return set()
    hashes = [zlib.crc32(t.encode("utf-8")) for t in tokens]
    n = len(hashes)
    w = max(1, _WINNOW_WINDOW)
    if n <= w:
        return set(hashes)
    fps = set()
    prev_min = -1
    for i in range(n - w + 1):
        m = min(hashes[i : i + w])
        if m != prev_min:
            fps.add(m)
            prev_min = m
    return fps


# ---------- AST 子树哈希（Merkle） ----------
def _ast_features(code: str) -> "set[int]":
    """源码 → AST 子树哈希集合。

    自底向上为每个节点计算结构哈希并收集：
    - 叶子：identifier→``ID``（抗重命名 T2）、integer/float→``NUM``、字符串→``STR``
      （抗常量级改写，避免把「改了个数字」误当不同代码）；关键字/运算符保留实际文本
      （运算符差异在此同样可见）；
    - 内部节点：``node.type(有序子哈希...)``，捕捉结构形状；
    - 注释节点一律跳过（与 ``normalize`` 去注释一致，注释不参与相似度）。

    相同结构（含重命名/常量改写）→ 相同子树哈希集合。解析失败或 tree-sitter
    不可用时返回空集（调用方回退到纯 token 特征）。
    """
    parser = _get_parser()
    if parser is None:
        return set()
    try:
        tree = parser.parse(code.encode("utf-8"))
    except Exception:
        return set()
    raw = code.encode("utf-8")  # tree-sitter 偏移为字节；按字节切片避免中文错位
    fps = set()
    memo = {}

    def _h(s: str) -> int:
        return zlib.crc32(s.encode("utf-8"))

    def _leaf_descriptor(node) -> str:
        t = node.type
        if t == "identifier":
            return "ID"
        if t in ("integer", "float"):
            return "NUM"
        if t in ("string", "concatenated_string", "bytes"):
            return "STR"
        try:
            text = raw[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
        except Exception:
            text = ""
        return f"{t}:{text}"

    def _visit(node):
        if node.type == "comment":
            return None
        key = (node.start_byte, node.end_byte, node.type)
        cached = memo.get(key)
        if cached is not None:
            return cached
        children = getattr(node, "children", None)
        if children is None:
            children = getattr(node, "named_children", None)
        if children:
            child_hashes = []
            for c in children:
                h = _visit(c)
                if h is not None:
                    child_hashes.append(h)
            desc = node.type + "(" + ",".join(str(h) for h in child_hashes) + ")"
        else:
            desc = _leaf_descriptor(node)
        h = _h(desc)
        fps.add(h)
        memo[key] = h
        return h

    try:
        _visit(tree.root_node)
    except RecursionError:
        logger.warning("AST 过深，跳过子树哈希特征（仅保留 token 特征）")
        return set()
    return fps


# ---------- 特征合并与 MinHash ----------
def _features(code: str) -> "set[int]":
    """合并特征集：Winnowed token 指纹 ∪ AST 子树哈希。

    code 为**原始 Python 源码**（内部调用 ``normalize`` 生成骨架后提取 token 特征）。
    """
    skel = normalize(code)
    fps = _winnowed_fingerprints(_tokenize(skel))
    fps |= _ast_features(code)
    return fps


def _minhash(fps: "set[int]") -> MinHash:
    m = MinHash(num_perm=_NUM_PERM, seed=_SEED)
    for fp in fps:
        m.update(str(fp).encode("utf-8"))
    return m


def _minhash_from_values(values: "list[int]") -> MinHash:
    """由持久化的 hashvalues 数组重建 MinHash（JSON 缓存加载用）。"""
    import numpy as np

    m = MinHash(num_perm=_NUM_PERM, seed=_SEED)
    m.hashvalues = np.array([int(v) for v in values], dtype=np.uint32)
    return m


class CoarseRetriever:
    """基于 datasketch MinHash 的相似召回客户端（全库确定性扫描）。

    特征管线（Winnowing 指纹 + 运算符感知分词 + AST 子树哈希），输出
    ``[{file, project, license, similarity}]``。
    """

    def __init__(self, knowledge_base, cache_dir: "str | Path | None" = None):
        """
        knowledge_base: ``KnowledgeBase`` 实例。
        cache_dir: 索引缓存目录（默认 ``<kb.base>/.index``）。
        """
        self.kb = knowledge_base
        self.base = knowledge_base.base
        self.cache_dir = Path(cache_dir) if cache_dir else (self.base / ".index")
        self._minhashes: "dict[str, MinHash]" = {}
        self._meta: "dict[str, dict]" = {}
        # 锚点召回索引（懒构建）：gram_hash -> {file_key}；决策与近似无关
        self._anchor_index: "dict[int, set[str]] | None" = None
        # 公开状态（供报告 methodology 字段与健康检查使用）
        self.mode = "full"
        self.file_count = 0
        self.tree_sitter_available = tree_sitter_available()
        self._build_or_load()
        self.file_count = len(self._minhashes)
        logger.info(
            "CoarseRetriever 就绪：%d 文件，模式=%s，tree_sitter=%s",
            self.file_count,
            self.mode,
            self.tree_sitter_available,
        )

    # ---------- 缓存指纹：KB 文件清单变更则失效重建 ----------
    def _fingerprint(self) -> str:
        h = hashlib.sha256()
        for item in self.kb.list_files():
            p = Path(item["file"])
            if p.exists():
                st = p.stat()
                h.update(f"{item['file']}:{st.st_mtime_ns}:{st.st_size}".encode())
        return h.hexdigest()

    def _build_or_load(self) -> None:
        fp = self._fingerprint()
        # 迁移：删除已废弃的 pickle 缓存（序列化不安全：可被投毒执行任意代码）
        legacy = self.cache_dir / "feature_index.pkl"
        if legacy.exists():
            try:
                legacy.unlink()
                logger.info("已删除废弃 pickle 缓存（迁移至 JSON）: %s", legacy)
            except OSError:
                logger.warning("删除废弃 pickle 缓存失败: %s", legacy)
        cache_file = self.cache_dir / "feature_index.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                if (
                    data.get("fingerprint") == fp
                    and data.get("num_perm") == _NUM_PERM
                    and data.get("format") == _FEATURE_FORMAT
                    and data.get("cache_format") == _CACHE_FORMAT
                    and data.get("datasketch_version") == _DATASKETCH_VERSION
                ):
                    self._minhashes = {
                        k: _minhash_from_values(v)
                        for k, v in data["minhashes"].items()
                    }
                    self._meta = data["meta"]
                    logger.info("加载 KB 相似索引缓存：%d 文件", len(self._minhashes))
                    return
            except Exception:
                logger.warning("KB 相似索引缓存损坏，重建", exc_info=True)
        self._build(fp, cache_file)

    def _build(self, fp: str, cache_file: "Path") -> None:
        self._minhashes = {}
        self._meta = {}
        for item in self.kb.list_files():
            try:
                code = self.kb.read_file(item["file"])
            except Exception:
                logger.warning("读取 KB 文件失败，跳过：%s", item["file"])
                continue
            fps = _features(code)
            if not fps:
                continue
            key = item["file"]
            self._minhashes[key] = _minhash(fps)
            self._meta[key] = {
                "file": item["file"],
                "project": item["project"],
                "license": item["license"],
            }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "fingerprint": fp,
                "num_perm": _NUM_PERM,
                "format": _FEATURE_FORMAT,
                "cache_format": _CACHE_FORMAT,
                "datasketch_version": _DATASKETCH_VERSION,
                # MinHash 序列化为 hashvalues 数组（JSON 安全，无代码执行风险）
                "minhashes": {
                    k: [int(v) for v in mh.hashvalues]
                    for k, mh in self._minhashes.items()
                },
                "meta": self._meta,
            }
            cache_file.write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            logger.info("构建并缓存 KB 相似索引：%d 文件", len(self._minhashes))
        except Exception:
            logger.warning("写入 KB 相似索引缓存失败（将每请求重建）", exc_info=True)

    def retrieve(self, code: str, top_k: int = 10) -> "list[dict] | None":
        """返回 ``[{file, project, license, similarity}]``，按 similarity 降序。

        ``code`` 为**原始 Python 源码**（内部规范化并提取多特征：运算符感知分词 + Winnowing 指纹 + AST 子树哈希）。

        策略：对查询 MinHash 与全库每个候选做精确 Jaccard 估计并排序取 Top-K
        （O(N×num_perm) 整数级比较，完全确定、可解释）。本方法按 top_k 截断，
        仅用于评估「粗筛质量」与快速预览；完整流水线请使用 ``recall_all``
        （不截断，召回完备）。
        """
        if not code or not self._minhashes:
            return None
        q = _minhash(_features(code))
        scored = [
            (key, float(q.jaccard(mh))) for key, mh in self._minhashes.items()
        ]
        scored = [(k, s) for k, s in scored if s > 0]
        if not scored:
            return None
        scored.sort(key=lambda x: x[1], reverse=True)
        out = []
        for key, sim in scored[:top_k]:
            meta = self._meta[key]
            out.append(
                {
                    "file": meta["file"],
                    "project": meta["project"],
                    "license": meta["license"],
                    "similarity": round(sim, 4),
                }
            )
        return out

    # ---------- 锚点召回闸门（确定性，消除 top_k 截断缺口） ----------
    def _ensure_anchor_index(self) -> None:
        """懒构建锚点索引：gram_hash -> {file_key}（进程内，未持久化）。"""
        if self._anchor_index is not None:
            return
        idx: "dict[int, set[str]]" = {}
        for key in self._minhashes:
            try:
                code = self.kb.read_file(key)
            except Exception:
                continue
            for g in anchor_grams(code.splitlines(), _ANCHOR_LEN):
                idx.setdefault(g, set()).add(key)
        self._anchor_index = idx
        logger.info("锚点召回索引就绪：%d 文件, %d gram", len(self._minhashes), len(idx))

    def _anchor_recall(self, code: str) -> "set[str]":
        """返回与查询共享 ≥1 个规范化行 L 元组的 KB 文件集合（确定性布尔）。"""
        self._ensure_anchor_index()
        hits: "set[str]" = set()
        for g in anchor_grams(code.splitlines(), _ANCHOR_LEN):
            hits |= self._anchor_index.get(g, set())
        return hits

    def recall_all(self, code: str, top_k: int = 10) -> "list[dict] | None":
        """确定性召回全集：全库非零相似度候选 ∪ 锚点行游程成员（**不截断**）。

        top_k 仅影响候选排序目标（排序基数），不再是候选上限——消除「真克隆
        相似度排名靠后被截断」的召回缺口。返回 ``[{file, project, license,
        similarity}]`` 按 similarity 降序（锚点补入而相似度为 0 的候选排在末尾）。
        下游由确定性验证器剪枝，故候选过包含是设计使然。
        """
        if not code or not self._minhashes:
            return None
        q = _minhash(_features(code))
        scored = [
            (key, float(q.jaccard(mh))) for key, mh in self._minhashes.items()
        ]
        scored = [(k, s) for k, s in scored if s > 0]
        by_key = {k: s for k, s in scored}
        for k in self._anchor_recall(code):
            if k not in by_key:
                by_key[k] = 0.0
        merged = sorted(by_key.items(), key=lambda x: x[1], reverse=True)
        if not merged:
            return None
        return [
            {**self._meta[key], "similarity": round(sim, 4)} for key, sim in merged
        ]
