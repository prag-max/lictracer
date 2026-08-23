# -*- coding: utf-8 -*-
"""生成 LicTracer 应用图标。

概念：已验证的代码盾牌 —— 深蓝渐变圆角应用底 + 白色盾牌内嵌 `</>` 码符
+ 右下角绿色验证勾。全部使用粗笔画矢量路径，无文字依赖，16px 仍可辨识。

产物：
- packaging/app.ico          多尺寸 ICO（256/128/64/48/32/24/16），exe 与窗口共用
- src/ui/assets/app.ico      运行时窗口图标（随包分发）
- docs/app_icon_preview.png  256px 预览图

运行：.venv\\Scripts\\python scripts\\make_icon.py
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parent.parent

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#3b82f6"/>
      <stop offset="1" stop-color="#1e40af"/>
    </linearGradient>
    <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="0.5" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- 应用底板 -->
  <rect x="8" y="8" width="240" height="240" rx="56" fill="url(#bg)"/>
  <rect x="8" y="8" width="240" height="132" rx="56" fill="url(#sheen)"/>

  <!-- 盾牌（白色实心，小尺寸对比度优先） -->
  <path d="M128 42 L198 70 V126 C198 172 167 199 128 214 C89 199 58 172 58 126 V70 Z"
        fill="#ffffff"/>

  <!-- 盾内代码符号 </> -->
  <g stroke="#1e40af" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="102,102 78,128 102,154" stroke-width="15"/>
    <polyline points="154,102 178,128 154,154" stroke-width="15"/>
    <line x1="140" y1="94" x2="116" y2="162" stroke-width="13"/>
  </g>

  <!-- 右下验证勾徽章 -->
  <circle cx="194" cy="192" r="36" fill="#16a34a" stroke="#ffffff" stroke-width="9"/>
  <polyline points="177,192 190,205 213,179" fill="none"
            stroke="#ffffff" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

SIZES = [256, 128, 64, 48, 32, 24, 16]


def render_pngs() -> dict[int, bytes]:
    """QtSvg 矢量渲染各尺寸，返回 {size: png_bytes}。"""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QByteArray, QRectF
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(QByteArray(SVG.encode("utf-8")))
    if not renderer.isValid():
        raise RuntimeError("SVG 无效")
    out: dict[int, bytes] = {}
    for s in SIZES:
        img = QImage(s, s, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(p, QRectF(0, 0, s, s))
        p.end()
        buf = QByteArray()
        from PySide6.QtCore import QBuffer, QIODevice

        w = QBuffer(buf)
        w.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(w, "PNG")
        w.close()
        out[s] = bytes(buf)
    return out


def main() -> None:
    from io import BytesIO

    from PIL import Image

    pngs = render_pngs()

    master = Image.open(BytesIO(pngs[256])).convert("RGBA")

    packaging_dir = REPO_ROOT / "packaging"
    assets_dir = REPO_ROOT / "src" / "ui" / "assets"
    docs_dir = REPO_ROOT / "docs"
    for d in (packaging_dir, assets_dir, docs_dir):
        d.mkdir(parents=True, exist_ok=True)

    ico_path = packaging_dir / "app.ico"
    master.save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
    )
    (assets_dir / "app.ico").write_bytes(ico_path.read_bytes())
    (assets_dir / "app_icon_256.png").write_bytes(pngs[256])
    (docs_dir / "app_icon_preview.png").write_bytes(pngs[256])

    print(f"icon written: {ico_path} ({ico_path.stat().st_size} bytes)")
    print(f"asset copied: {assets_dir / 'app.ico'}")


if __name__ == "__main__":
    main()
