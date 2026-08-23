# -*- coding: utf-8 -*-
"""证据精炼层 —— 使用真实 redup 做查询代码与候选文件的细粒度比对。

调用 redup 的跨项目对比能力 ``redup.core.comparator.compare_projects``，把查询
代码（单文件）与候选文件（各自来源项目）做结构性/相似性比对，输出行级证据
``{file, project, license, line_start, line_end, similarity}``。

工程加固（对齐技术栈评估）：
- **调用缓存**：相同查询+相同候选集合（按内容/时间戳/大小指纹）直接复用结果，
  避免每次分析重复走 redup 的多进程比对与临时目录 I/O；
- **参数可配**：``LICT_REDUP_FUNCTIONS_ONLY``（默认 1，仅函数级比对）、
  ``LICT_REDUP_MIN_SIM``（默认 0.3，redup 内部质量过滤）与
  ``LICT_REDUP_MIN_LINES``（默认 3，**计数式闸门**）可经环境变量覆盖。

**裁决语义（确定性等价架构）**：本层为**补充性行级证据**，不再担任克隆裁决
（裁决由 ``exact_verifier`` 的 L1/L2/L3 布尔判定完成）。证据闸门由「相似度
比例 ≥ 0.5」改为「命中行数 ≥ ``LICT_REDUP_MIN_LINES``」——比例会混同
「小函数整段复制」与「大文件部分复制」，计数式更可辩护且无浮点裁决。

**已知局限（诚实声明）**：``functions_only=True`` 仅比对函数级匹配，模块级语句、
类属性等非函数结构的克隆可能不产生证据；redup 的相似度口径与粗筛层的 MinHash
估计值是两套度量，本层输出仅作细粒度行级区间参考。
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tempfile
from collections import OrderedDict
from pathlib import Path

from redup.core.comparator import compare_projects

logger = logging.getLogger("lictracer.evidence")

# redup 内部质量过滤（低于此相似度的匹配不产生证据；非裁决阈值）
_MIN_SIMILARITY = float(os.environ.get("LICT_REDUP_MIN_SIM", "0.3"))
# 计数式证据闸门：命中行数达到此值才算行级证据（替代旧 0.5 比例裁决）
_MIN_LINES = int(os.environ.get("LICT_REDUP_MIN_LINES", "3"))
# 仅函数级比对（可配：设为 0/false 则文件级全量比对）
_FUNCTIONS_ONLY = os.environ.get("LICT_REDUP_FUNCTIONS_ONLY", "1").lower() in (
    "1",
    "true",
    "yes",
)
# 调用缓存上限（FIFO 淘汰，防内存膨胀）
_CACHE_MAX = 64
_REFINE_CACHE: "OrderedDict[str, list]" = OrderedDict()


def _cache_key(query_lines: "list[str]", candidates: "list[dict]") -> str:
    """缓存键：查询内容 + 候选文件（路径:修改时间:大小）指纹。"""
    h = hashlib.sha256()
    h.update("\n".join(query_lines).encode("utf-8", errors="replace"))
    for c in candidates:
        p = Path(c["file"])
        try:
            st = p.stat()
            sig = f"{c['file']}:{st.st_mtime_ns}:{st.st_size}"
        except OSError:
            sig = f"{c['file']}:missing"
        h.update(sig.encode())
    return h.hexdigest()


def refine(query_lines: "list[str]", candidates: "list[dict]") -> "list[dict]":
    """对每个候选文件做行级对比，输出统一证据列表。

    query_lines: 查询代码行列表；candidates: ``[{file, project, license, similarity}]``。
    返回 ``[{file, project, license, line_start, line_end, similarity}]``，
    其中 ``line_start``/``line_end`` 为查询代码内的行号范围。
    """
    if not query_lines or not candidates:
        return []

    key = _cache_key(query_lines, candidates)
    cached = _REFINE_CACHE.get(key)
    if cached is not None:
        _REFINE_CACHE.move_to_end(key)
        return [dict(x) for x in cached]  # 返回副本，避免调用方污染缓存

    result = _refine_impl(query_lines, candidates)

    _REFINE_CACHE[key] = result
    while len(_REFINE_CACHE) > _CACHE_MAX:
        _REFINE_CACHE.popitem(last=False)
    return [dict(x) for x in result]


def _refine_impl(query_lines: "list[str]", candidates: "list[dict]") -> "list[dict]":
    with tempfile.TemporaryDirectory() as _qd, tempfile.TemporaryDirectory() as _cd:
        query_dir = Path(_qd)
        cand_dir = Path(_cd)

        # 查询代码落盘为单一项目
        query_file = query_dir / "__query__.py"
        query_file.write_text("\n".join(query_lines), encoding="utf-8")

        # 候选文件拷贝到另一项目目录，按序号命名并保留映射
        name_to_candidate: "dict[str, dict]" = {}
        for idx, cand in enumerate(candidates):
            src = Path(cand["file"])
            if not src.exists():
                continue
            dst = cand_dir / f"{idx}_{src.name}"
            shutil.copy2(src, dst)
            name_to_candidate[dst.name] = cand

        comparison = compare_projects(
            query_dir,
            cand_dir,
            similarity_threshold=_MIN_SIMILARITY,
            min_lines=1,
            functions_only=_FUNCTIONS_ONLY,
        )

        evidence = []
        for match in comparison.matches:
            if float(match.similarity) < _MIN_SIMILARITY:
                continue
            # 计数式闸门：命中行数 ≥ min_lines（替代旧 0.5 比例裁决）
            start, end = match.lines_a
            if int(end) - int(start) + 1 < _MIN_LINES:
                continue
            # file_a 属于 project_a（查询侧），file_b 属于 project_b（候选侧）
            cand = name_to_candidate.get(Path(match.file_b).name)
            if cand is None:
                continue
            evidence.append(
                {
                    "file": cand["file"],
                    "project": cand.get("project"),
                    "license": cand.get("license"),
                    "line_start": int(start),
                    "line_end": int(end),
                    "similarity": round(float(match.similarity), 4),
                    "match_type": "redup_line",
                }
            )
        return evidence
