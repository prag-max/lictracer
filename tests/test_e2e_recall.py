# -*- coding: utf-8 -*-
"""端到端召回 / 确定性 / 合规准确率达标断言（受控基准 data/benchmark）。

复用 evaluation.run_eval 的评估逻辑（两层召回 + 确定性证据率 + 合规准确率），
断言在受控基准上：
- 粗筛召回 / 粗筛精确率 / 端到端召回 / 端到端精确率 / 合规准确率 全部 == 1.00
- 确定性证据率 == 1.00：正样本均由 L1/L2 布尔结构判定裁决（决策路径无浮点阈值）
- 负样本零假阳性（e2e_source 为 None）

确定性等价验证器（exact_verifier）替代旧结构克隆兜底（e2e_clone_threshold 0.30）
后，near-miss 改写克隆(transformed) 由 L2 函数体规范语句序列包含裁决，
端到端召回 / 确定性证据率 / 合规准确率均达 1.00，且不依赖相似度阈值。
"""
import json
import logging
import sys
from pathlib import Path

import pytest

# evaluation/ 非已安装包（仅开发 harness），测试内引导项目根到 sys.path（测试专属，非源码 hack）
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import evaluation.run_eval as _ev  # noqa: E402

# run_eval 在模块顶层 logging.disable(CRITICAL)，import 后恢复全局日志状态，避免影响其他测试
logging.disable(logging.NOTSET)


pytestmark = pytest.mark.slow  # 受控基准全量重建（分钟级）：默认跳过，CI 全量通道运行


@pytest.fixture(scope="module")
def results():
    _ev.main()
    p = _ev.BENCH / "results.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_benchmark_metrics_all_one(results):
    s = results["summary"]
    assert s["coarse_retrieval"]["recall"] == pytest.approx(1.0)
    assert s["coarse_retrieval"]["precision"] == pytest.approx(1.0)
    assert s["end2end_retrieval"]["recall"] == pytest.approx(1.0)
    assert s["end2end_retrieval"]["precision"] == pytest.approx(1.0)
    assert s["compatibility_accuracy"] == pytest.approx(1.0)


def test_attribution_accuracy_one(results):
    """主证据融合（布尔级 × 相似度排序）归属准确率 1.00：单源正样本主证据源
    均命中预期源且无归属歧义；多源复合查询（cross_file，多来源证据强度并列）
    的歧义标记正确触发（属预期行为）。"""
    s = results["summary"]
    assert s["end2end_retrieval"]["attribution_accuracy"] == pytest.approx(1.0)
    for r in results["rows"]:
        if r["kind"] == "negative":
            continue
        exp = r["expected_project"]
        multi = isinstance(exp, list)
        assert r["attribution_correct"] is True, f"{r['id']} 主证据源归属错误"
        if not multi:
            assert r["attribution_ambiguous"] is False, (
                f"{r['id']} 存在不同来源 (level, sim) 完全并列的归属歧义"
            )


def test_positive_evidence_is_deterministic(results):
    """正样本必须由 L1/L2 布尔结构判定裁决（确定性证据率 1.00，无阈值依赖）。"""
    s = results["summary"]
    assert s["end2end_retrieval"]["deterministic_rate"] == pytest.approx(1.0)
    for r in results["rows"]:
        if r["kind"] != "negative":
            assert r["e2e_level"] in (1, 2), (
                f"正样本 {r['id']} 未获 L1/L2 确定性验证（level={r['e2e_level']}）"
            )


def test_negative_no_false_positive(results):
    for r in results["rows"]:
        if r["kind"] == "negative":
            assert r["e2e_source"] is None, f"负样本 {r['id']} 被验证器误判为克隆"
            assert r["e2e_relevant"] is True


def test_e2e_recall_by_kind_transformed_one(results):
    b = results["summary"]["by_kind"]["transformed"]
    assert b is not None
    assert b["e2e_relevant"] == pytest.approx(1.0)
    assert b["deterministic_rate"] == pytest.approx(1.0)
    assert b["compat_acc"] == pytest.approx(1.0)
