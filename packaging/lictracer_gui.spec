# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：LicTracer 桌面端（Windows onedir）。

构建方式：仓库根执行 packaging/build_exe.ps1
产物形态：dist/LicTracer/LicTracer.exe + _internal/（整目录分发，可 zip）

资源布局约定（与 src/config.py 的 _app_root() 对齐）：
- config/                    → _internal/config/          （settings.yaml / license_rules.yaml）
- data/knowledge_base/       → _internal/data/knowledge_base/ （内置默认 KB）
- osadl_matrix 数据文件      → _internal/osadl_matrix/…   （collect_data_files 自动收集）

frozen 态下 sys._MEIPASS 即 _internal/，相对路径规则与开发态一致，
故 src.config 的 PROJECT_ROOT / knowledge_base_path() 无需特殊分支即可寻址。

发布自检：LicTracer.exe --selfcheck → 读 exe 同目录 selfcheck_result.txt。
"""
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# spec 内相对路径以本文件目录（packaging/）为基准；collect_submodules 需要能导入 src，
# 故把仓库根（spec 目录的上一级）加入构建期 sys.path。
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPECPATH)))
sys.path.insert(0, _REPO_ROOT)

osadl_datas = collect_data_files("osadl_matrix")

# 强制收录整个 src 包：入口 launcher 只静态引用 src.ui.main，
# 显式枚举可杜绝「包内模块因 pathex 语义未入 PYZ」的启动即炸问题。
src_modules = collect_submodules("src")

# 第三方依赖显式兜底（均为纯 Python 包，不产生 _internal 目录，
# 历史上曾因静态分析断链而缺失；列全以防万一）。
third_party = [
    "redup",
    "datasketch",
    "license_expression",
    "boolean",  # license_expression 依赖
    "semantic_version",  # license_expression 依赖
]

a = Analysis(
    ["launcher.py"],
    pathex=[".."],
    binaries=[],
    datas=[
        ("..\\config", "config"),
        ("..\\data\\knowledge_base", "data\\knowledge_base"),
        ("..\\src\\ui\\assets", "src/ui/assets"),
    ]
    + osadl_datas,
    hiddenimports=src_modules
    + third_party
    + [
        # tree-sitter 原生扩展与其语言包（.pyd 在包内，需显式声明确保收集）
        "tree_sitter",
        "tree_sitter_python",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",  # 未使用，减小体积
        "pydoc_data",
        # 注意：不可排除 unittest —— datasketch → scipy → numpy.testing 运行时链
        # 需要 unittest，排除会导致 frozen 启动即 ModuleNotFoundError。
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

# 调试开关：LICT_DEBUG_CONSOLE=1 构建带控制台的变体，启动报错时可直接看到 traceback。
debug_console = os.environ.get("LICT_DEBUG_CONSOLE", "0") == "1"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LicTracer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX 易触发杀软误报，保持关闭
    console=debug_console,  # 默认窗口应用无控制台；调试变体为 True
    icon="app.ico",  # 应用图标（位于本 spec 同目录，由 scripts/make_icon.py 生成）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LicTracer",
)
