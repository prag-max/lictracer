# -*- coding: utf-8 -*-
"""界面图标工厂：内联 SVG → 可着色 QIcon（矢量，随主题缩放不糊）。

用法：icon("play", color="#ffffff") 返回 18px QIcon。
资源解析 frozen 兼容：assets 目录在开发态位于 src/ui/assets，
打包后经 config._app_root() 定位到 _internal/src/ui/assets。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from src.config import _app_root

# 粗描边线性风格（stroke={c} 为颜色占位符）
_SVGS: dict[str, str] = {
    "folder": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
        <path d='M3 7a2 2 0 0 1 2-2h4l2.2 2.5H19a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z'/></svg>""",
    "search": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round'>
        <circle cx='11' cy='11' r='7'/><line x1='20' y1='20' x2='16.5' y2='16.5'/></svg>""",
    "play": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='{c}'>
        <path d='M8 5.5v13a1 1 0 0 0 1.54.84l10-6.5a1 1 0 0 0 0-1.68l-10-6.5A1 1 0 0 0 8 5.5Z'/></svg>""",
    "stop": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='{c}'>
        <rect x='6' y='6' width='12' height='12' rx='2'/></svg>""",
    "export": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
        <path d='M12 3v12'/><path d='m7 10 5 5 5-5'/>
        <path d='M4 19h16'/></svg>""",
    "shield": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linejoin='round'>
        <path d='M12 3 20 6v6c0 5-3.5 8-8 9.5C7.5 20 4 17 4 12V6Z'/></svg>""",
    "check_circle": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
        <circle cx='12' cy='12' r='9'/><path d='m8.5 12 2.5 2.5 4.5-5'/></svg>""",
    "alert": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
        <path d='M12 3 22 20H2Z'/><line x1='12' y1='10' x2='12' y2='14'/>
        <circle cx='12' cy='17' r='0.6' fill='{c}'/></svg>""",
    "settings": """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
        stroke='{c}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
        <circle cx='12' cy='12' r='3'/>
        <path d='M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06
                 a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09
                 A1.7 1.7 0 0 0 8.9 19.4a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1
                 -2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1
                 0-4h.09A1.7 1.7 0 0 0 4.6 8.9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1
                 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1
                 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1
                 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V9a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1
                 0 4h-.09a1.7 1.7 0 0 0-1.51 1Z'/></svg>""",
}


def icon(name: str, color: str = "#475569", size: int = 18) -> QIcon:
    """按名称与颜色生成矢量 QIcon。"""
    tpl = _SVGS.get(name)
    if tpl is None:
        return QIcon()
    svg = tpl.replace("{c}", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    img = QImage(size * 2, size * 2, QImage.Format.Format_ARGB32)  # 2x 抗模糊
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p, QRectF(0, 0, size * 2, size * 2))
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(2.0)
    return QIcon(pm)


def app_icon() -> QIcon:
    """应用窗口图标（多尺寸 ICO；frozen 下经 _app_root 定位）。"""
    candidates = [
        Path(__file__).resolve().parent / "assets" / "app.ico",
        _app_root() / "src" / "ui" / "assets" / "app.ico",
    ]
    for c in candidates:
        if c.exists():
            return QIcon(str(c))
    return app_icon_fallback()


def app_icon_fallback() -> QIcon:
    """资产缺失时的兜底：直接用内联 shield SVG 渲染。"""
    ic = icon("shield", color="#2563eb", size=64)
    return ic


def asset_path(name: str) -> Path | None:
    """定位 assets 资源文件（开发态 / frozen 双兼容）。"""
    for c in (Path(__file__).resolve().parent / "assets" / name,
              _app_root() / "src" / "ui" / "assets" / name):
        if c.exists():
            return c
    return None
