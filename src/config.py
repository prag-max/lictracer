# -*- coding: utf-8 -*-
"""集中式配置加载：settings.yaml / license_rules.yaml。

所有加载均内建默认值降级，保证在未安装 pyyaml 的纯标准库环境下也能运行。
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("lictracer.config")


def _app_root() -> Path:
    """应用资源根目录（config/ 与 data/ 的定位基准）。

    - 开发态：仓库根（src/config.py 的上两级）；
    - PyInstaller frozen：``sys._MEIPASS``（onedir 形态即 ``dist/LicTracer/_internal``，
      config/ 与 data/knowledge_base 随包置于其下，相对路径规则与开发态完全一致）。
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _app_root()
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

# 默认设置（当 settings.yaml 缺失或 yaml 不可用时）
_DEFAULT_SETTINGS = {
    "project_license": "MIT",
    "knowledge_base_path": "data/knowledge_base",
    "rules_config_path": "config/license_rules.yaml",
    "top_k": 10,
    "link_type": "dynamic",
    "log_level": "INFO",
}

# 默认 Copyleft 规则（当 license_rules.yaml 缺失或 yaml 不可用时）
_DEFAULT_RULES = {
    "copyleft_rules": [
        {"license_pattern": "GPL-*", "link_type": "static", "action": "project_must_open_source"},
        {"license_pattern": "GPL-*", "link_type": "dynamic", "action": "segment_only"},
        {"license_pattern": "AGPL-*", "link_type": "dynamic", "action": "project_must_open_source"},
        {"license_pattern": "LGPL-*", "link_type": "dynamic", "action": "segment_only"},
    ]
}


def _load_env_if_available() -> None:
    """可选加载 .env（python-dotenv），失败静默跳过。"""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        logger.debug("加载 .env 失败（python-dotenv 不可用或文件缺失），忽略", exc_info=True)


def _read_yaml(path: Path) -> dict:
    """读取 YAML 文件；无 yaml 库或解析失败时抛出异常由调用方兜底。"""
    import yaml  # type: ignore

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _resolve(rel_path) -> Path:
    """把相对项目根的路径解析为绝对路径。"""
    p = Path(rel_path)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def load_settings() -> dict:
    """加载系统配置。文件缺失或 yaml 不可用时返回默认配置。"""
    _load_env_if_available()
    settings = dict(_DEFAULT_SETTINGS)
    try:
        data = _read_yaml(CONFIG_DIR / "settings.yaml")
        settings.update(data)
    except Exception:
        logger.warning("读取 settings.yaml 失败，使用默认配置", exc_info=True)
    # 环境变量覆盖（如 KNOWLEDGE_BASE_PATH）
    for key in ("knowledge_base_path", "rules_config_path", "project_license"):
        env = os.environ.get(key.upper())
        if env:
            settings[key] = env
    return settings


def load_license_rules() -> dict:
    """加载 Copyleft 策略配置，失败返回默认规则。"""
    settings = load_settings()
    try:
        rules_path = _resolve(settings.get("rules_config_path", "config/license_rules.yaml"))
        data = _read_yaml(rules_path)
        if "copyleft_rules" in data:
            return data
    except Exception:
        logger.warning("读取 license_rules.yaml 失败，使用默认 Copyleft 规则", exc_info=True)
    return dict(_DEFAULT_RULES)


def knowledge_base_path() -> Path:
    """解析知识库根目录绝对路径。"""
    return _resolve(load_settings().get("knowledge_base_path", "data/knowledge_base"))
