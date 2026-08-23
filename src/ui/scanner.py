# -*- coding: utf-8 -*-
"""文件夹扫描与筛选（纯函数、无 Qt 依赖，便于单元测试）。"""
from __future__ import annotations

import os
from pathlib import Path

# 递归扫描时默认跳过的目录名（虚拟环境 / 版本库 / IDE / 构建与缓存产物）
DEFAULT_EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    ".tox",
}


def scan_python_files(
    root, exclude_dirs=None, suffix=".py"
) -> "list[Path]":
    """递归扫描 root 下指定后缀的文件（默认 ``*.py``），返回排序后的绝对路径列表。

    非目录输入返回空列表；排除目录按名字整层剪枝（不进入，故大目录下开销可控）。
    """
    root = Path(root)
    if not root.is_dir():
        return []
    excl = DEFAULT_EXCLUDE_DIRS if exclude_dirs is None else set(exclude_dirs)
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in excl)
        for fn in sorted(filenames):
            if fn.endswith(suffix):
                out.append(Path(dirpath) / fn)
    return out


def filter_by_text(paths, query) -> "list[Path]":
    """按子串过滤（匹配完整路径或文件名，大小写不敏感）；空查询原样返回。"""
    q = (query or "").strip().lower()
    if not q:
        return list(paths)
    return [p for p in paths if q in str(p).lower()]
