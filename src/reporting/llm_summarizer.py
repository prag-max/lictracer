# -*- coding: utf-8 -*-
"""报告生成层 —— 自然语言摘要（LLM 仅作“翻译官”，不参与合规判断）。

工程加固（对齐技术栈评估）：
- **指数退避重试**：对 429/5xx 等临时错误自动重试（默认 2 次），优先遵循
  ``Retry-After`` 响应头；
- **可配超时**：``LICT_LLM_TIMEOUT``（默认 30 秒）；
- **审计日志**：记录 provider/model/耗时/尝试次数，不记录任何许可证或来源细节；
- **可选来源脱敏**：``LICT_LLM_MASK_SOURCE=1`` 时把片段来源替换为「来源N」再外发。
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

logger = logging.getLogger("lictracer.reporting")

# 默认重试次数与初始退避（秒）
_MAX_RETRIES = 2
_BACKOFF_BASE = 1.0


def _template(rule_result: dict) -> str:
    """无 API Key 时的固定中文模板摘要。"""
    status = rule_result.get("status")
    risk = rule_result.get("risk_level")
    reason = rule_result.get("reason", "")
    segments = rule_result.get("segments", [])
    src_desc = "、".join(
        f"{s.get('source')}/{s.get('license')}" for s in segments if s.get("source")
    ) or "无"
    risk_cn = {"LOW": "低", "MEDIUM": "中", "HIGH": "高"}.get(risk, risk)
    status_cn = {
        "COMPATIBLE": "兼容",
        "INCOMPATIBLE": "不兼容",
        "NEEDS_REVIEW": "需复核",
    }.get(status, status)
    return (
        f"本次审计共识别出 {len(segments)} 个来源片段（来源：{src_desc}），"
        f"合规结论为「{status_cn}」，风险等级「{risk_cn}」。{reason}"
    )


def _masked_payload(rule_result: dict) -> dict:
    """外发前构造最小化载荷；按需把来源替换为「来源N」脱敏。"""
    mask = os.environ.get("LICT_LLM_MASK_SOURCE", "").lower() in ("1", "true", "yes")
    segments = rule_result.get("segments", [])
    if mask:
        segments = [
            {**s, "source": f"来源{idx + 1}"} for idx, s in enumerate(segments)
        ]
    return {
        "status": rule_result.get("status"),
        "risk_level": rule_result.get("risk_level"),
        "reason": rule_result.get("reason"),
        "segments": segments,
    }


def _post(url: str, payload_bytes: bytes, headers: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=payload_bytes, headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_llm(rule_result: dict) -> str:
    """调用 OpenAI / DeepSeek 兼容 API 生成摘要；失败抛异常由调用方兜底。

    重试策略：429/5xx 等临时错误按指数退避重试（尊重 ``Retry-After``）。
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")

    if openai_key:
        provider = "openai"
        api_key = openai_key
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    elif deepseek_key:
        provider = "deepseek"
        api_key = deepseek_key
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = os.environ.get("DEEPSEEK_MODEL", "deepseek-v3")
    else:
        raise RuntimeError("无可用 API Key")

    timeout = float(os.environ.get("LICT_LLM_TIMEOUT", "30"))
    system_prompt = (
        "你是一个合规审计报告的翻译官。请把下面的结构化结论用中文转述为一段自然语言摘要，"
        "只做转述，不要修改或补充任何合规判断。"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        _masked_payload(rule_result),
                        ensure_ascii=False,
                        default=str,
                    ),
                },
            ],
            "temperature": 0,
        }
    ).encode("utf-8")

    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    delay = _BACKOFF_BASE
    for attempt in range(_MAX_RETRIES + 1):
        t0 = time.monotonic()
        try:
            data = _post(url, payload, headers, timeout)
            text = data["choices"][0]["message"]["content"].strip()
            logger.info(
                "LLM 摘要成功：provider=%s model=%s 耗时=%.2fs",
                provider,
                model,
                time.monotonic() - t0,
            )
            return text
        except urllib.error.HTTPError as exc:
            # 4xx（除 429 外）为确定性错误，不重试
            if exc.code < 500 and exc.code != 429:
                logger.warning(
                    "LLM 摘要确定性失败：provider=%s code=%s", provider, exc.code
                )
                raise
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            logger.warning(
                "LLM 摘要临时失败（code=%s），%.1fs 后第 %d 次重试",
                exc.code,
                wait,
                attempt + 2,
            )
            if attempt >= _MAX_RETRIES:
                raise
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM 摘要请求失败（%s: %s），%.1fs 后第 %d 次重试",
                type(exc).__name__,
                exc,
                delay,
                attempt + 2,
            )
            if attempt >= _MAX_RETRIES:
                raise
            time.sleep(delay)
        delay *= 2
    raise RuntimeError("LLM 调用失败")


def summarize(rule_result: dict) -> str:
    """生成自然语言摘要。

    安全/隐私说明：启用 LLM 后，结构化结论中的来源项目、许可证、原因等信息
    会通过 ``user_prompt`` 发送给第三方 API（OpenAI / DeepSeek），存在专有代码
    片段信息外发风险。默认关闭，仅当显式设置 ``LICT_ENABLE_LLM=1/true/yes``
    时才调用 LLM；否则一律使用本地固定模板，不外发任何数据。
    设置 ``LICT_LLM_MASK_SOURCE=1`` 可对来源做脱敏后再外发。
    """
    llm_enabled = os.environ.get("LICT_ENABLE_LLM", "").lower() in ("1", "true", "yes")
    if llm_enabled and (
        os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    ):
        try:
            text = _call_llm(rule_result)
            if text:
                return text
        except Exception:
            logger.warning("LLM 摘要生成失败，回退本地模板", exc_info=True)
    return _template(rule_result)
