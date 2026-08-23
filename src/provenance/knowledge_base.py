# -*- coding: utf-8 -*-
"""溯源层 —— 知识库管理与文件扫描。

扫描 ``data/knowledge_base/projects/`` 下所有 ``.py`` 文件，结合
``licenses.json`` 得到每个项目的许可证。

加固（对齐技术栈评估）：
- ``licenses.json`` 结构/内容校验（非法键、空许可证值 → 告警并按 UNKNOWN 处理）；
- 未映射许可证的项目在扫描时一次性 WARNING 告警，避免静默 UNKNOWN。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("lictracer.provenance")


class KnowledgeBase:
    """精选高复用基准代码库：文件列表 + 项目许可证映射。"""

    def __init__(self, path):
        # 接受 str 或 Path
        self.base = Path(path)
        self.projects_dir = self.base / "projects"
        self.licenses = self._load_licenses()
        self._files = None

    def _load_licenses(self) -> dict:
        """加载并校验 项目名 -> SPDX 许可证 映射。"""
        p = self.base / "licenses.json"
        data = {}
        if p.exists():
            try:
                loaded = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
                else:
                    logger.warning("licenses.json 顶层结构应为 dict，忽略")
            except Exception:
                logger.warning("licenses.json 解析失败，按空映射处理", exc_info=True)
        else:
            logger.warning("licenses.json 缺失，所有项目许可证按 UNKNOWN 处理")

        cleaned = {}
        for key, value in data.items():
            if not isinstance(key, str) or not key.strip():
                logger.warning("licenses.json 含非法项目键，跳过: %r", key)
                continue
            key = key.strip()
            if not isinstance(value, str) or not value.strip():
                logger.warning(
                    "licenses.json 项目 %r 的许可证为空，按 UNKNOWN 处理", key
                )
                cleaned[key] = "UNKNOWN"
                continue
            cleaned[key] = value.strip()
        return cleaned

    def _scan(self) -> None:
        """扫描知识库文件，缓存结果；未映射许可证的项目一次性告警。"""
        files = []
        missing = set()
        if self.projects_dir.exists():
            for py in sorted(self.projects_dir.rglob("*.py")):
                project = py.parent.name  # projects/<project>/xxx.py
                lic = self.get_license(project)
                if lic == "UNKNOWN":
                    missing.add(project)
                files.append(
                    {
                        "file": str(py),
                        "project": project,
                        "license": lic,
                    }
                )
        if missing:
            logger.warning(
                "以下知识库项目未在 licenses.json 中映射许可证，将按 UNKNOWN 处理: %s",
                sorted(missing),
            )
        self._files = files

    def list_files(self) -> "list[dict]":
        """返回 [{file, project, license}, ...]。"""
        if self._files is None:
            self._scan()
        return list(self._files)

    def get_license(self, project: str) -> str:
        """返回项目对应的许可证；未映射返回 "UNKNOWN"。"""
        return self.licenses.get(project, "UNKNOWN")

    def read_file(self, file_path: str) -> str:
        """按路径读取知识库文件内容。"""
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
