# -*- coding: utf-8 -*-
"""合规推理层 —— Copyleft 传染判断（YAML 驱动）。"""
from __future__ import annotations

import fnmatch

from src.config import load_license_rules


def _rules():
    cfg = load_license_rules()
    return cfg.get("copyleft_rules", [])


def is_copyleft(license_text: str) -> bool:
    """判断许可证是否为 copyleft 家族（GPL / AGPL / LGPL）。"""
    key = (license_text or "").upper()
    return any(k in key for k in ("GPL", "AGPL", "LGPL"))


def _match_pattern(pattern: str, license_text: str) -> bool:
    if "*" in pattern:
        return fnmatch.fnmatch(license_text.upper(), pattern.upper())
    return pattern.upper() == license_text.upper()


def assess(license_text: str, link_type: str = "dynamic") -> dict:
    """评估某个许可证在给定链接方式下的 Copyleft 传染后果。

    返回 ``{copyleft: bool, action: str|None, description: str}``。
    """
    result = {
        "copyleft": is_copyleft(license_text),
        "action": None,
        "description": "",
    }
    if not result["copyleft"]:
        result["description"] = f"{license_text} 非 Copyleft 许可证，无传染性。"
        return result

    best_action = None
    for rule in _rules():
        pattern = rule.get("license_pattern", "")
        if not _match_pattern(pattern, license_text):
            continue
        rule_link = rule.get("link_type")
        # 无 link_type 的规则（如 AGPL）任意链接方式都命中；否则按链接方式匹配
        if rule_link is None or rule_link == link_type:
            best_action = rule.get("action")
            break

    if best_action == "project_must_open_source":
        result["action"] = best_action
        result["description"] = (
            f"{license_text} 为强 Copyleft 许可证，传染性触发，整个项目须以兼容的开源许可证发布。"
        )
    elif best_action == "segment_only":
        result["action"] = best_action
        result["description"] = (
            f"{license_text} 为 Copyleft 许可证，仅该片段及其衍生代码须保持开源。"
        )
    else:
        result["action"] = "segment_only"
        result["description"] = f"{license_text} 属于 Copyleft 家族，存在传染风险。"
    return result
