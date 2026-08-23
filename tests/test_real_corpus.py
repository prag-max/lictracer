# -*- coding: utf-8 -*-
"""真实开源语料基准（data/benchmark_real）的端到端指标达标断言。

与 test_e2e_recall（受控合成基准）互补：本基准的 KB 实体来自**本机已安装的
真实开源包**（click / datasketch / license_expression / charset_normalizer /
numpy / pandas）用 tree-sitter 提取的真实函数 / 类片段，改写变体与合成基准
一致（exact / renamed / transformed / deleted / reordered / class_attr）。

断言（真实代码分布下的稳健属性，均由确定性等价验证器保证）：
- 粗筛召回 / 精确率、端到端召回 / 精确率、合规准确率 == 1.00
- 确定性证据率 == 1.00：正样本均由 L1/L2/L3 布尔结构判定裁决（无浮点阈值）
- 负样本零假阳性（经锚点行游程非碰撞过滤，不与任何 KB 实体共享 ≥3 连续规范行）

已知残差（已在文档明示、不作为失败断言）：真实跨项目代码可能存在**结构近邻**
（两份真实代码结构相似），此时验证器必能检出克隆（正确项目仍在证据中，
e2e 召回不受影响），但来源归属可能同时指向结构相似的他包（top 证据源归属歧义）。
合规结论因本基准所选许可证（BSD/MIT/Apache）均与 MIT 参考项目兼容而不受影响。
"""
import json
import logging
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import evaluation.real_corpus as _rc  # noqa: E402
import evaluation.run_eval as _ev  # noqa: E402

logging.disable(logging.NOTSET)  # run_eval 顶层静默日志，import 后恢复


pytestmark = pytest.mark.slow  # 真实语料基准构建耗时（~35min）：默认跳过，CI 全量通道运行


@pytest.fixture(scope="module")
def results():
    _rc.main()  # 生成真实语料基准（可重复：覆盖写）
    _ev.main("benchmark_real")
    p = ROOT / "data" / "benchmark_real" / "results.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_real_benchmark_metrics_all_one(results):
    """真实语料基准上四指标（粗筛 / 端到端 / 合规）全部 == 1.00。"""
    s = results["summary"]
    assert s["coarse_retrieval"]["recall"] == pytest.approx(1.0)
    assert s["coarse_retrieval"]["precision"] == pytest.approx(1.0)
    assert s["end2end_retrieval"]["recall"] == pytest.approx(1.0)
    assert s["end2end_retrieval"]["precision"] == pytest.approx(1.0)
    assert s["compatibility_accuracy"] == pytest.approx(1.0)


def test_real_attribution_accuracy_one(results):
    """真实语料主证据融合归属准确率 1.00：弱 L3 伪匹配不再扰动归属（次优证据融合），
    全部正样本主证据源命中预期源、无归属歧义。"""
    s = results["summary"]
    assert s["end2end_retrieval"]["attribution_accuracy"] == pytest.approx(1.0)
    for r in results["rows"]:
        assert r["attribution_ambiguous"] is False, (
            f"{r['id']} 存在不同来源 (level, sim) 完全并列的归属歧义"
        )
        if r["kind"] != "negative":
            assert r["attribution_correct"] is True, f"{r['id']} 主证据源归属错误"


def test_real_positive_evidence_is_deterministic(results):
    """真实语料正样本必须由 L1/L2/L3 布尔判定裁决（确定性证据率 1.00）。"""
    s = results["summary"]
    assert s["end2end_retrieval"]["deterministic_rate"] == pytest.approx(1.0)
    for r in results["rows"]:
        if r["kind"] != "negative":
            assert r["e2e_level"] in (1, 2, 3), (
                f"真实语料正样本 {r['id']} 未获 L1/L2/L3 确定性验证（level={r['e2e_level']}）"
            )


def test_real_negative_no_false_positive(results):
    """真实语料负样本零假阳性（非碰撞过滤后不应与任何 KB 实体共享锚点游程）。"""
    negs = [r for r in results["rows"] if r["kind"] == "negative"]
    assert len(negs) == 8, f"负样本数异常: {len(negs)}"
    for r in negs:
        assert r["e2e_source"] is None, f"负样本 {r['id']} 被验证器误判为克隆"
        assert r["e2e_relevant"] is True


def test_real_recall_by_rewrite_kind(results):
    """真实语料按改写类型细分：全部类型端到端召回 / 确定性率 / 合规 == 1.00。"""
    for kind in ("exact", "renamed", "transformed", "deleted", "reordered", "class_attr"):
        b = results["summary"]["by_kind"][kind]
        assert b is not None and b["n"] >= 1, f"类型 {kind} 无查询"
        assert b["coarse_relevant"] == pytest.approx(1.0), f"{kind} 粗筛召回 < 1.0"
        assert b["e2e_relevant"] == pytest.approx(1.0), f"{kind} 端到端召回 < 1.0"
        assert b["deterministic_rate"] == pytest.approx(1.0), f"{kind} 确定性率 < 1.0"
        assert b["compat_acc"] == pytest.approx(1.0), f"{kind} 合规准确率 < 1.0"
