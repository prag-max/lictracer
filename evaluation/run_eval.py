# -*- coding: utf-8 -*-
"""LicTracer 评估 harness —— 在受控基准上量化检索、确定性与合规指标。

读取 data/benchmark/ground_truth.json + queries，逐条评估，输出：
  - 粗筛召回 (coarse)：CoarseRetriever.retrieve 层（多特征 MinHash）top1 是否命中预期源
  - 端到端召回 (e2e)：完整流水线 segments（确定性验证器裁决）是否保留预期源
  - 确定性证据率 (deterministic)：正样本是否由 L1/L2 布尔结构判定裁决（无浮点阈值）
  - 合规准确率 (compat)：compliance_result.status == ground truth

输出 data/benchmark/results.json。
"""
from __future__ import annotations

import argparse
import json
import logging
import statistics
import time
from pathlib import Path

logging.disable(logging.CRITICAL)  # 静默引擎日志，仅看指标

from src.pipeline import analyze_text
from src.provenance.coarse_retriever import CoarseRetriever
from src.provenance.knowledge_base import KnowledgeBase

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmark"  # 默认合成基准目录

# 负样本判定阈值：粗筛 top1 相似度达到此值且命中某源，视为"错误召回"（假阳性）
NEG_SIM_THRESHOLD = 0.30
TOP_K = 10


def _top_segment(report: dict) -> "dict | None":
    """返回主证据段：优先取流水线主证据融合的结果（attribution.primary_source），
    缺失时按 (verification_level 最小, similarity 最高) 兜底。"""
    segs = report.get("segments") or []
    if not segs:
        return None
    prim = (report.get("attribution") or {}).get("primary_source")
    if prim is not None:
        for s in segs:
            if s.get("source") == prim:
                return s
    return max(
        segs,
        key=lambda s: (-(s.get("verification_level") or 99), s.get("similarity") or 0.0),
    )


def evaluate_one(gt: dict, code: str, rt: CoarseRetriever, kb_path: str) -> dict:
    # 粗筛层（retrieve，多特征 MinHash）
    coarse = rt.retrieve(code, top_k=TOP_K)
    coarse_top = max(coarse, key=lambda c: c["similarity"]) if coarse else None
    # 注意：retrieve 返回键为 "project"（segment_aggregator 才映射为 "source"）
    coarse_source = coarse_top.get("project") if coarse_top else None
    coarse_sim = coarse_top.get("similarity", 0.0) if coarse_top else 0.0

    # 端到端（完整流水线，含确定性验证器裁决）
    report = analyze_text(
        code, kb_path=kb_path, project_license="MIT", top_k=TOP_K, include_summary=False
    )
    segs = report.get("segments") or []
    top = _top_segment(report)
    e2e_sources = [s.get("source") for s in segs if s.get("source")]
    e2e_levels = [s.get("verification_level") for s in segs if s.get("verification_level")]
    e2e_source = e2e_sources[0] if e2e_sources else None
    # 最强（最小）确定性级别代表本案证据强度
    e2e_level = min(e2e_levels) if e2e_levels else None
    comp_status = (report.get("compliance_result") or {}).get("status")

    kind = gt["kind"]
    expected_project = gt.get("expected_project")
    expected_compat = gt.get("expected_compat")
    exp_set = expected_project if isinstance(expected_project, list) else [expected_project]

    # 主证据归属（次优证据融合：布尔判定级 × 相似度排序 → primary_source）
    attrib = report.get("attribution") or {}
    primary_source = attrib.get("primary_source")
    attribution_ambiguous = bool(attrib.get("attribution_ambiguous"))
    # 归属准确：正样本主证据源 ∈ 预期源集合（多源取任一）
    attribution_correct = kind != "negative" and primary_source in exp_set

    # ---- 粗筛召回判定 ----
    if kind == "negative":
        coarse_relevant = not (coarse_source and coarse_sim >= NEG_SIM_THRESHOLD)
    else:
        coarse_relevant = coarse_source in exp_set

    # ---- 端到端召回判定（多源：所有预期源均被召回） ----
    if kind == "negative":
        e2e_relevant = len(e2e_sources) == 0
    else:
        e2e_relevant = all(s in e2e_sources for s in exp_set)

    compat_correct = comp_status == expected_compat
    # 确定性证据：正样本由 L1/L2/L3（布尔结构/锚点判定）裁决，不依赖相似度阈值
    e2e_deterministic = kind != "negative" and e2e_level in (1, 2, 3)

    return {
        "id": gt["id"],
        "kind": kind,
        "expected_project": expected_project,
        "expected_compat": expected_compat,
        "coarse_source": coarse_source,
        "coarse_sim": round(coarse_sim, 4),
        "e2e_source": e2e_source,
        "e2e_sim": round(top.get("similarity", 0.0), 4) if top else 0.0,
        "e2e_level": e2e_level,
        "primary_source": primary_source,
        "attribution_ambiguous": attribution_ambiguous,
        "attribution_correct": attribution_correct,
        "compliance_status": comp_status,
        "coarse_relevant": coarse_relevant,
        "e2e_relevant": e2e_relevant,
        "compat_correct": compat_correct,
        "e2e_deterministic": e2e_deterministic,
    }


def _aggregate(rows, key, positives_only=False):
    sub = [r for r in rows if (r["kind"] != "negative") or not positives_only]
    if not sub:
        return 0.0
    return sum(r[key] for r in sub) / len(sub)


def main(bench_name: str = "benchmark") -> None:
    """在指定基准（data/<bench_name>）上量化检索 / 确定性 / 合规指标。

    ``bench_name="benchmark"`` 为受控合成基准；``"benchmark_real"`` 为真实开源
    语料基准（由 evaluation.real_corpus 生成）。结果写入 data/<bench_name>/results.json。
    """
    bench = ROOT / "data" / bench_name
    gt_doc = json.loads((bench / "ground_truth.json").read_text(encoding="utf-8"))
    kb_path = str(bench / "kb")
    queries = gt_doc["queries"]

    # 构建检索器（warmup，复用 analyze_text 内部缓存）
    rt = CoarseRetriever(KnowledgeBase(kb_path))

    rows = []
    latencies = []
    for gt in queries:
        code = (bench / "queries" / gt["id"]).read_text(encoding="utf-8")
        t0 = time.perf_counter()
        row = evaluate_one(gt, code, rt, kb_path)
        latencies.append(time.perf_counter() - t0)
        row["latency_s"] = round(latencies[-1], 4)
        rows.append(row)

    positives = [r for r in rows if r["kind"] != "negative"]
    negatives = [r for r in rows if r["kind"] == "negative"]

    def _metrics(rel_key):
        recall = _aggregate(positives, rel_key)
        precision = _aggregate(rows, rel_key)  # 整体相关比例（含负样本无假召回）
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0
        return recall, precision, f1

    coarse_recall, coarse_prec, coarse_f1 = _metrics("coarse_relevant")
    e2e_recall, e2e_prec, e2e_f1 = _metrics("e2e_relevant")
    compat_acc = _aggregate(rows, "compat_correct")
    # 确定性证据率：正样本中由 L1/L2 布尔结构判定裁决的比例（不依赖相似度阈值）
    det_rate = _aggregate(positives, "e2e_deterministic")
    # 归属准确率：正样本主证据源（布尔级 × 相似度联合决策）命中预期源的比例
    attr_acc = _aggregate(positives, "attribution_correct")

    def _by(kind):
        sub = [r for r in rows if r["kind"] == kind]
        if not sub:
            return None
        return {
            "n": len(sub),
            "coarse_relevant": sum(r["coarse_relevant"] for r in sub) / len(sub),
            "e2e_relevant": sum(r["e2e_relevant"] for r in sub) / len(sub),
            "compat_acc": sum(r["compat_correct"] for r in sub) / len(sub),
            "attribution_acc": (
                sum(r["attribution_correct"] for r in sub) / len(sub)
                if kind != "negative"
                else None
            ),
            "deterministic_rate": (
                sum(r["e2e_deterministic"] for r in sub) / len(sub)
                if kind != "negative"
                else None
            ),
        }

    summary = {
        "kb_path": kb_path,
        "n_queries": len(rows),
        "n_positive": len(positives),
        "n_negative": len(negatives),
        "coarse_retrieval": {
            "recall": round(coarse_recall, 4),
            "precision": round(coarse_prec, 4),
            "f1": round(coarse_f1, 4),
        },
        "end2end_retrieval": {
            "recall": round(e2e_recall, 4),
            "precision": round(e2e_prec, 4),
            "f1": round(e2e_f1, 4),
            "deterministic_rate": round(det_rate, 4),
            "attribution_accuracy": round(attr_acc, 4),
        },
        "compatibility_accuracy": round(compat_acc, 4),
        "by_kind": {
            "exact": _by("exact"),
            "renamed": _by("renamed"),
            "transformed": _by("transformed"),
            "deleted": _by("deleted"),
            "reordered": _by("reordered"),
            "class_attr": _by("class_attr"),
            "cross_file": _by("cross_file"),
            "negative": _by("negative"),
        },
        "latency": {
            "per_query_mean_s": round(statistics.mean(latencies), 4),
            "per_query_median_s": round(statistics.median(latencies), 4),
            "per_query_p95_s": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 4),
            "note": "含端到端溯源+确定性验证+合规；检索器已预热",
        },
        "neg_sim_threshold": NEG_SIM_THRESHOLD,
    }

    (bench / "results.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=" * 68)
    print("LicTracer 受控基准评估结果（两层召回 + 合规 + 确定性证据率）")
    print("=" * 68)
    print(f"查询总数: {summary['n_queries']} (正={summary['n_positive']}, 负={summary['n_negative']})")
    c, e = summary["coarse_retrieval"], summary["end2end_retrieval"]
    print(f"[粗筛层 多特征 MinHash] Recall={c['recall']:.4f} Precision={c['precision']:.4f} F1={c['f1']:.4f}")
    print(f"[端到端 含验证] Recall={e['recall']:.4f} Precision={e['precision']:.4f} F1={e['f1']:.4f}")
    print(f"[确定性证据率] : {e['deterministic_rate']:.4f} (L1/L2 布尔判定占比, 正样本)")
    print(f"[归属准确率]   : {e['attribution_accuracy']:.4f} (主证据融合: 布尔级×相似度排序, 正样本)")
    print(f"[合规准确率]    : {summary['compatibility_accuracy']:.4f}")
    print("-" * 68)
    print("逐类 (粗筛recall / 端到端recall / 归属acc / 确定性率 / 合规acc):")
    for k in ("exact", "renamed", "transformed", "deleted", "reordered", "class_attr", "cross_file", "negative"):
        b = summary["by_kind"][k]
        if b:
            det = "  -  " if b["deterministic_rate"] is None else f"{b['deterministic_rate']:.3f}"
            attr = "  -  " if b["attribution_acc"] is None else f"{b['attribution_acc']:.3f}"
            print(f"  {k:12s} n={b['n']:2d}  coarse={b['coarse_relevant']:.3f}  e2e={b['e2e_relevant']:.3f}  attr={attr}  det={det}  compat={b['compat_acc']:.3f}")
    print("-" * 68)
    lat = summary["latency"]
    print(f"延迟/查询 mean={lat['per_query_mean_s']}s median={lat['per_query_median_s']}s p95={lat['per_query_p95_s']}s")
    print("=" * 68)
    print(f"详细 -> {bench / 'results.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LicTracer 评估 harness")
    parser.add_argument(
        "--bench", default="benchmark",
        help="基准目录名（data/<bench>）；benchmark=合成, benchmark_real=真实语料",
    )
    args = parser.parse_args()
    main(args.bench)
