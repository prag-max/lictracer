# -*- coding: utf-8 -*-
"""合规推理层 —— 许可证标准化为 SPDX 标识（对齐 osadl-matrix 的键）。"""
from __future__ import annotations

import logging

logger = logging.getLogger("lictracer.compliance")

try:
    from license_expression import Licensing  # type: ignore

    _LICENSING = Licensing()
except Exception:
    _LICENSING = None
    logger.warning("license-expression 不可用，许可证标准化降级为原文回退", exc_info=True)

# 已告警过的原文（只警告一次，避免重复刷日志）
_WARNED_RAW: "set[str]" = set()


# SPDX 废弃的裸标识 → 现行 ``-only`` 形式（osadl-matrix 只认 `-only`/`-or-later`）
_BARE_TO_ONLY = {
    "GPL-1.0": "GPL-1.0-only",
    "GPL-2.0": "GPL-2.0-only",
    "GPL-3.0": "GPL-3.0-only",
    "LGPL-2.0": "LGPL-2.0-only",
    "LGPL-2.1": "LGPL-2.1-only",
    "LGPL-3.0": "LGPL-3.0-only",
    "AGPL-1.0": "AGPL-1.0-only",
    "AGPL-3.0": "AGPL-3.0-only",
}


def normalize(license_text: str) -> str:
    """把许可证标识标准化为 SPDX 标识。

    - ``GPL-3.0`` 这类裸标识 → ``GPL-3.0-only``；
    - ``GPL-3.0+`` → ``GPL-3.0-or-later``；
    - ``MIT``、``Apache-2.0`` 等已是 SPDX 标识则原样返回；
    - 无法解析时返回清洗后的原文（后续矩阵查询会落到 UNKNOWN）。
    """
    if not license_text:
        return "UNKNOWN"

    text = str(license_text).strip()
    key = None
    if _LICENSING is not None:
        try:
            parsed = _LICENSING.parse(text)
            if parsed is not None:
                key = str(parsed)
        except Exception:
            key = None
    if not key:
        # 无法解析：按原文回退（后续矩阵查询会落到 UNKNOWN）；只告警一次
        key = text
        if text not in _WARNED_RAW:
            _WARNED_RAW.add(text)
            logger.warning(
                "许可证标识无法解析为 SPDX，按原文回退（可能非法或未收录）: %r",
                text,
            )

    key = key.strip()

    # ``GPL-3.0+`` 等旧式 ``+`` 写法 → ``-or-later``
    if key.endswith("+"):
        key = key[:-1] + "-or-later"

    # 裸 copyleft 标识 → ``-only``
    return _BARE_TO_ONLY.get(key, key)
