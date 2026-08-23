# -*- coding: utf-8 -*-
"""混合许可证基准（benchmark_mixed）——量化「主证据驱动的合规聚合」的误报下降。

背景：真实跨项目代码存在结构近邻（弱 L3 锚点匹配 / 小段 L2 包含、相似度
0.09–0.17）。若这些**弱伪匹配段**参与合规结论，其高危害许可证（GPL-2.0 /
MPL-2.0 / LGPL-3.0，与 MIT 参考项目不兼容）会把本应 COMPATIBLE 的结论误升级为
INCOMPATIBLE / NEEDS_REVIEW —— 合规误报。

本基准构造：
- KB = 真实 6 包（BSD/MIT/Apache，兼容）+ **3 个真实 GPL/MPL/LGPL 干扰项目**
  （distractor-gpl=beancount(GPL-2.0) / distractor-mpl=mozinfo(MPL-2.0) /
  distractor-lgpl=python-telegram-bot(LGPL-3.0)，与 MIT 不兼容）；
- 干扰实体 = 真实包中与真实 6 包目标实体**自然存在 L3 锚点弱匹配**的函数
  （≥3 连续规范行重叠、非 L1/L2 完整结构）——真实跨项目结构近邻，
  弱伪匹配会把高危害许可证误升级为 INCOMPATIBLE（合规误报）；
- 负样本经确定性验证器零匹配过滤（覆盖真实 + 干扰全部实体）。

评估（同一查询、同一 KB）：
- **旧聚合**：rule_engine 对**全部段**做保守聚合（改动前行为）——弱 GPL/MPL
  伪匹配段 → 误报 INCOMPATIBLE / NEEDS_REVIEW；
- **新聚合**：流水线主证据驱动——强段 L1/L2 + 主证据段参与结论，其余弱段
  （非主证据的 L3/4）仅展示 → 保持 COMPATIBLE；
- 量化：误报查询数（旧 vs 新）、被消除的误报、剩余误报、归属准确率。

输出 data/benchmark_mixed/results.json（含 escalation_cases.json 明细）。
运行：``python -m evaluation.benchmark_mixed``
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logging.disable(logging.CRITICAL)

import tree_sitter as _ts  # type: ignore
import tree_sitter_python as _tspy  # type: ignore

from src.compliance.rule_engine import evaluate as _rule_evaluate
from src.pipeline import analyze_text
from src.provenance.exact_verifier import verify as _verify

import evaluation.real_corpus as _rc

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmark_mixed"

# 真实 GPL/MPL/LGPL 开源包（干扰项目源码，从 PyPI wheel 解压归档在 data/raw_sources/）
REAL_DISTRACTOR_PACKAGES = {
    "distractor-gpl": {
        "license": "GPL-2.0",
        "src_dir": ROOT / "data" / "raw_sources" / "beancount",
        "pkg": "beancount",
    },
    "distractor-lgpl": {
        "license": "LGPL-3.0",
        "src_dir": ROOT / "data" / "raw_sources" / "telegram",
        "pkg": "telegram",
    },
    "distractor-mpl": {
        "license": "MPL-2.0",
        "src_dir": ROOT / "data" / "raw_sources" / "mozinfo",
        "pkg": "mozinfo",
    },
}


def _extract_dir(src_dir: Path, parser) -> "list[dict]":
    """从本地源码目录（PyPI sdist 解压后）提取中等规模函数实体（含装饰器）。"""
    funcs: list[dict] = []
    if not src_dir.exists():
        return funcs
    for py in sorted(src_dir.rglob("*.py")):
        try:
            code = py.read_text(encoding="utf-8")
            raw = code.encode("utf-8")
        except Exception:
            continue
        if b"\x00" in raw:
            continue
        tree = parser.parse(raw)
        for node in _rc._walk(tree.root_node):
            if node.type != "function_definition":
                continue
            name = _rc._node_name(node, raw)
            if not name or name.startswith("__") or name in _rc.COMMON_NAMES:
                continue
            body = _rc._named_body(node)
            if not (5 <= len(body) <= 60):
                continue
            parent = node.parent
            slice_from = parent if (parent and parent.type == "decorated_definition") else node
            funcs.append({"kind": "func", "name": name,
                          "src": _rc._slice(slice_from, raw), "n": len(body)})
    return funcs


# 混合基准的目标包 = 原 6 个兼容真实包（与干扰项目 beancount/telegram/mozinfo
# 不重叠——扩充后的 real_corpus.TARGET_PACKAGES 已含 GPL/LGPL/MPL 包，不能复用）
MIXED_TARGET_PACKAGES = [
    "click",
    "datasketch",
    "license_expression",
    "charset_normalizer",
    "numpy",
    "pandas",
]


def build_distractors(parser) -> "dict[str, dict]":
    """干扰项目 = **真实 GPL/MPL/LGPL 开源包实体**（替换 v4 的合成片段干扰）。

    筛选：真实函数与真实 6 包目标实体**自然存在 L3 锚点弱匹配**（≥3 连续规范行
    重叠、非 L1/L2 完整结构）才保留为干扰实体——L3 是「召回闸门」过包含设计，
    弱伪匹配会把高危害许可证误升级为 INCOMPATIBLE，正属于本基准要量化的误报。
    与目标无任何弱匹配的真实函数（结构差异大）丢弃。
    """
    targets: list[dict] = []
    for pkg in MIXED_TARGET_PACKAGES:
        funcs, _classes, _lic = _rc.extract_package(pkg, parser)
        targets.extend({"pkg": pkg, "name": e["name"], "src": e["src"]} for e in funcs)
    if not targets:
        return {}

    out: dict[str, dict] = {}
    for key, cfg in REAL_DISTRACTOR_PACKAGES.items():
        picked: list[dict] = []
        for e in _extract_dir(cfg["src_dir"], parser):
            for t in targets:
                v = _verify(e["src"], t["src"], t["src"].splitlines(), e["src"].splitlines())
                if v is not None and v["verification_level"] == 3:
                    picked.append(e)
                    break
        if picked:
            out[key] = {"license": cfg["license"], "entities": picked}
    return out


def _evaluate_one(gt: dict, code: str, kb_path: str) -> dict:
    """对单条查询对比旧 / 新聚合的合规结论与归属。"""
    report = analyze_text(
        code, kb_path=kb_path, project_license="MIT", top_k=10, include_summary=False
    )
    status_new = report["compliance_result"]["status"]
    conclusion_ids = report["compliance_result"].get("conclusion_segment_ids", [])
    segs = report.get("segments") or []
    # 旧聚合：改动前行为 = rule_engine 对全部段保守聚合
    status_old = _rule_evaluate(list(segs), "MIT")["status"]

    expected = gt["expected_compat"]
    old_wrong = status_old != expected
    new_wrong = status_new != expected
    eliminated = old_wrong and not new_wrong

    primary = (report.get("attribution") or {}).get("primary_source")
    exp = gt["expected_project"]
    exp_set = exp if isinstance(exp, list) else [exp]
    attr_correct = gt["kind"] != "negative" and primary in exp_set

    excluded = [s for s in segs if s["id"] not in conclusion_ids]
    return {
        "id": gt["id"],
        "kind": gt["kind"],
        "expected_compat": expected,
        "status_old": status_old,
        "status_new": status_new,
        "old_wrong": old_wrong,
        "new_wrong": new_wrong,
        "eliminated": eliminated,
        "primary_source": primary,
        "attr_correct": attr_correct,
        "conclusion_sources": [s["source"] for s in segs if s["id"] in conclusion_ids],
        "excluded_weak": [
            {"source": s.get("source"), "license": s.get("license"),
             "level": s.get("verification_level"), "similarity": s.get("similarity")}
            for s in excluded
        ],
    }


def main() -> None:
    parser = _ts.Parser(_ts.Language(_tspy.language()))
    extra = build_distractors(parser)
    print(f"干扰项目: {list(extra.keys())}")
    for k, v in extra.items():
        print(f"  {k:16s} license={v['license']:10s} entities={len(v['entities'])}")

    _rc.build_benchmark(
        BENCH, extra_projects=extra or None, target_packages=MIXED_TARGET_PACKAGES
    )
    gt_doc = json.loads((BENCH / "ground_truth.json").read_text(encoding="utf-8"))
    kb_path = str(BENCH / "kb")

    rows = []
    for gt in gt_doc["queries"]:
        code = (BENCH / "queries" / gt["id"]).read_text(encoding="utf-8")
        rows.append(_evaluate_one(gt, code, kb_path))

    positives = [r for r in rows if r["kind"] != "negative"]
    old_wrong = [r for r in rows if r["old_wrong"]]
    new_wrong = [r for r in rows if r["new_wrong"]]
    eliminated = [r for r in rows if r["eliminated"]]
    attr_acc = sum(r["attr_correct"] for r in positives) / len(positives) if positives else 0.0

    summary = {
        "bench": "mixed_license",
        "n_queries": len(rows),
        "n_positive": len(positives),
        "n_negative": len(rows) - len(positives),
        "old_aggregation_wrong": len(old_wrong),
        "new_aggregation_wrong": len(new_wrong),
        "eliminated_false_escalations": len(eliminated),
        "remaining_wrong": len(new_wrong),
        "attribution_accuracy": round(attr_acc, 4),
        "note": (
            "旧聚合=全部段参与结论（改动前行为）；新聚合=主证据驱动（强段 L1/L2 + "
            "主证据段参与，其余弱段仅展示）。误报 = 合规结论 != ground truth COMPATIBLE。"
        ),
    }

    (BENCH / "results.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (BENCH / "escalation_cases.json").write_text(
        json.dumps(
            [
                {
                    "id": r["id"],
                    "status_old": r["status_old"],
                    "status_new": r["status_new"],
                    "conclusion_sources": r["conclusion_sources"],
                    "excluded_weak": r["excluded_weak"],
                }
                for r in eliminated
            ],
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 68)
    print("混合许可证基准：主证据驱动合规聚合的误报下降")
    print("=" * 68)
    print(f"查询: {summary['n_queries']} (正={summary['n_positive']}, 负={summary['n_negative']})")
    print(f"[旧聚合(全段参与)] 结论错误: {summary['old_aggregation_wrong']} 条")
    print(f"[新聚合(主证据驱动)] 结论错误: {summary['new_aggregation_wrong']} 条")
    print(f"[被消除的误报]       : {summary['eliminated_false_escalations']} 条")
    print(f"[归属准确率]         : {summary['attribution_accuracy']:.4f}")
    print("-" * 68)
    for r in eliminated[:12]:
        srcs = ",".join(str(x) for x in r["excluded_weak"][:2])
        print(f"  {r['id']:46s} old={r['status_old']:12s} new={r['status_new']:12s} 弱段={srcs}")
    print(f"详细 -> {BENCH / 'results.json'} / escalation_cases.json")


if __name__ == "__main__":
    main()
