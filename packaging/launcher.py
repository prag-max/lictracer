# -*- coding: utf-8 -*-
"""PyInstaller 入口启动器（薄壳）。

为什么需要它：直接以 src/ui/main.py 作为 Analysis 脚本时，包内模块的
绝对导入（from src.xxx import ...）在 frozen 分析中易因 pathex 相对语义
而整体丢失 src 包。本文件位于仓库根，`from src.ui.main import main`
以仓库根为基准触发完整静态分析；配合 spec 中 collect_submodules('src')
强制收录全部 src 子模块。
"""
from src.ui.main import main

if __name__ == "__main__":
    raise SystemExit(main())
