# -*- coding: utf-8 -*-
"""流水线编排器 —— 串联 预处理 → 溯源召回 → 证据精炼 → 多源聚合 → 合规推理 → 报告。

这是 CLI / API / UI 共用的单一入口。
"""
from __future__ import annotations

from pathlib import Path

from src.aggregator.segment_aggregator import aggregate
from src.compliance.matrix_loader import warn_if_osadl_snapshot_stale
from src.compliance.rule_engine import evaluate
from src.config import knowledge_base_path, load_settings
from src.evidence.redup_adapter import refine
from src.preprocessor.ast_normalizer import original_lines, tree_sitter_available
from src.provenance.coarse_retriever import CoarseRetriever
from src.provenance.exact_verifier import verify_candidates
from src.provenance.knowledge_base import KnowledgeBase
from src.reporting.llm_summarizer import summarize
from src.reporting.report_builder import build

# 进程内检索器缓存：避免每次分析重建 MinHash 索引（KB 规模下重建代价高）
_RETRIEVER_CACHE: "dict[str, CoarseRetriever]" = {}


def rank_primary(segments: "list[dict]") -> "list[dict]":
    """主证据融合排序（次优证据融合）：段均为确定性验证（布尔判定）产物，
    在其上按 (similarity 最高, verification_level 最小, source 字典序) 排序，
    段[0] 为主证据段（``is_primary=True``）。

    联合决策 = **布尔判定先门控**（L1/L2/L3 任一命中才成段）＋ **相似度排序**
    （在已验证段中，相似度最高者为主证据源）。相似度主导的理由：真实跨项目
    场景下，小段结构伪匹配（L2 包含）的相似度远低于正确来源的锚点游程
    （L3），仅按布尔级排序会把伪匹配误判为主证据；相似度是 MinHash 估计值
    （±7.4%），仅用于排序与展示、不参与克隆裁决，与既有设计一致。
    决策路径仍无浮点阈值（相似度只在已验证段之间做相对排序）。
    """

    def _key(s):
        return (
            -float(s.get("score") or 0.0),
            s.get("verification_level") if s.get("verification_level") is not None else 99,
            str(s.get("source") or ""),
        )

    segs = sorted(segments, key=_key)
    for i, s in enumerate(segs):
        s["is_primary"] = i == 0
    return segs


def attribution_of(segments: "list[dict]") -> dict:
    """主证据归属：返回 ``{primary_source, attribution_ambiguous}``。

    歧义 = 存在**不同来源**的段与主证据段在 (verification_level, similarity) 上
    完全并列（精确相等，无阈值）；同源多段（同一 KB 文件多行区间）不计歧义。
    歧义不静默——报告显式标记 ``attribution_ambiguous=True``，由审计者复核。
    """
    if not segments:
        return {"primary_source": None, "attribution_ambiguous": False}
    primary = segments[0]
    p_lvl = primary.get("verification_level")
    p_sim = float(primary.get("score") or 0.0)
    ambiguous = any(
        (s.get("source") != primary.get("source"))
        and (s.get("verification_level") == p_lvl)
        and (float(s.get("score") or 0.0) == p_sim)
        for s in segments[1:]
    )
    return {"primary_source": primary.get("source"), "attribution_ambiguous": ambiguous}


# 参与合规结论的强证据验证级：L1 规范型精确相等 / L2 结构语句序列包含
_STRONG_LEVELS = (1, 2)


def select_conclusion_segments(segments: "list[dict]") -> "list[dict]":
    """**主证据驱动的合规聚合**：从全部确定性验证段中选出「参与合规结论」的段。

    规则（阈值无关，基于验证级布尔分档 + 主证据融合排序）：
    - **强证据段（L1/L2）全部参与结论**——L1/L2 为全序列结构匹配（规范型相等 /
      完整语句序列包含），是可信的克隆裁决；多源强段并存（如跨文件复合）时
      保留 rule_engine 的保守聚合（任一 NO/UNKNOWN → 升级）；
    - **主证据段（rank_primary 的段[0]，相似度最高的已验证段）始终参与结论**——
      即使其验证级为 L3（仅命中锚点游程的语句删除 / 重排变体），它仍是最强
      证据，被排除结论不可辩护；
    - **其余弱证据段（非主证据的 L3/4）仅作报告展示、不参与结论**——L3 锚点
      行游程是「召回闸门」（过包含设计）、L4 为 redup 行级补充证据，弱伪匹配
      （真实跨项目结构近邻，相似度 0.09–0.17）若参与结论会把高危害许可证
      （GPL/MPL 等）误升级为 INCOMPATIBLE / NEEDS_REVIEW，产生合规误报。

    返回被标记 ``drives_conclusion=True`` 的段（输入段原地加标记）。
    """
    for s in segments:
        s["drives_conclusion"] = False
    if not segments:
        return []
    chosen = [s for s in segments if s.get("verification_level") in _STRONG_LEVELS]
    primary = segments[0]  # 主证据融合已排序，段[0] 为主证据段
    if id(primary) not in {id(s) for s in chosen}:
        chosen.append(primary)
    for s in chosen:
        s["drives_conclusion"] = True
    return chosen


def _get_retriever(kb_path) -> CoarseRetriever:
    """按 KB 路径复用检索器实例（含磁盘 MinHash 索引缓存）。"""
    key = str(kb_path)
    rt = _RETRIEVER_CACHE.get(key)
    if rt is None:
        rt = CoarseRetriever(KnowledgeBase(kb_path))
        _RETRIEVER_CACHE[key] = rt
    return rt


def analyze_file(
    path,
    *,
    project_license=None,
    top_k=None,
    kb_path=None,
    min_anchor_lines=None,
    include_summary=True,
) -> dict:
    """分析单个 .py 文件，返回完整报告 dict。

    所有参数均可由 config/settings.yaml 提供，也可显式覆盖（便于测试与复用）；
    ``min_anchor_lines`` 供桌面端高级选项覆盖 L3 锚点游程门槛，缺省取 settings。
    """
    settings = load_settings()
    # 方法学边界可见化：OSADL 快照时效告警（离线、每进程至多一次，不影响结论）
    warn_if_osadl_snapshot_stale()

    if project_license is None:
        project_license = settings.get("project_license", "MIT")
    if top_k is None:
        top_k = int(settings.get("top_k", 10))
    if kb_path is None:
        kb_path = knowledge_base_path()
    kb_path = Path(kb_path)
    if min_anchor_lines is None:
        min_anchor_lines = settings.get("min_anchor_lines", 3)

    code = Path(path).read_text(encoding="utf-8")

    # 1. 预处理：原始行列表（供证据；溯源层内部自行规范化并提取多特征：运算符感知分词 + Winnowing 指纹 + AST 子树哈希）
    query_lines = original_lines(code)

    # 2. 溯源召回（多特征 MinHash 排序 + 锚点召回闸门；recall_all 不截断 top_k，
    #    消除「相似度排名靠后被截断」的召回缺口）
    nl_client = _get_retriever(kb_path)
    candidates = nl_client.recall_all(code, top_k=top_k)

    # 3. 证据精炼（行级, redup）——补充性细粒度证据，不再担任裁决
    evidence = refine(query_lines, candidates)

    # 3.5 确定性等价验证（替代旧 e2e_clone_threshold 0.30 结构兜底，决策路径无浮点阈值）：
    #   L1 规范型精确相等（T1/T2）/ L2 函数体规范语句序列包含（T3）/ L3 锚点行游程。
    #   已获 redup 证据的文件补记 verification_level；未覆盖的文件补确定性证据。
    min_anchor = int(min_anchor_lines)
    verdicts = verify_candidates(
        candidates,
        nl_client.kb.read_file,
        code,
        query_lines,
        min_anchor_lines=min_anchor,
    )
    _covered = {e["file"] for e in evidence}
    for v in verdicts:
        f = v["file"]
        if f in _covered:
            for e in evidence:
                if e["file"] == f:
                    e["verification_level"] = min(
                        e.get("verification_level", 99), v["verification_level"]
                    )
        else:
            evidence.append(v)
            _covered.add(f)
    # 无确定性验证的 redup 证据标记级别 4（行级证据，非 L1/L2/L3 验证）
    for e in evidence:
        e.setdefault("verification_level", 4)

    # 4. 多源聚合 + 主证据融合（次优证据融合：布尔判定级 × 相似度排序 → 主证据源）
    segments = aggregate(evidence)
    segments = rank_primary(segments)
    attribution = attribution_of(segments)

    # 5. 合规推理（主证据驱动的合规聚合：强证据段 L1/L2 参与结论；
    #    无强段时主证据段单独驱动；弱证据段 L3/4 仅作报告展示、不参与结论）
    link_type = settings.get("link_type", "dynamic")
    conclusion_segments = select_conclusion_segments(segments)
    rule_result = evaluate(conclusion_segments, project_license, link_type=link_type)

    # 6. 报告生成
    report = build(rule_result, segments, evidence)
    report["attribution"] = attribution
    report["compliance_result"]["conclusion_segment_ids"] = [
        s["id"] for s in conclusion_segments
    ]
    report["compliance_result"]["conclusion_note"] = (
        "合规结论由强证据段（L1 规范型精确相等 / L2 结构语句序列包含）驱动；"
        "无强证据时由主证据段（相似度最高的已验证段）单独驱动；"
        "弱证据段（L3 锚点行游程 / L4 行级证据）仅作报告展示、不参与结论。"
    )
    # 方法学声明：降级/近似状态可见化（不静默改变结果）
    report["methodology"] = {
        "tree_sitter": "available" if tree_sitter_available() else "fallback_regex",
        "retriever_mode": getattr(nl_client, "mode", "unknown"),
        "kb_files": getattr(nl_client, "file_count", None),
        "verification_min_anchor_lines": min_anchor,
    }
    if include_summary:
        report["nl_summary"] = summarize(rule_result)
    return report


def analyze_text(
    code: str,
    *,
    project_license=None,
    top_k=None,
    kb_path=None,
    include_summary=True,
) -> dict:
    """直接分析代码文本（无文件时使用）。"""
    import tempfile

    with tempfile.NamedTemporaryFile(
        "w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp = f.name
    try:
        return analyze_file(
            tmp,
            project_license=project_license,
            top_k=top_k,
            kb_path=kb_path,
            include_summary=include_summary,
        )
    finally:
        Path(tmp).unlink(missing_ok=True)
