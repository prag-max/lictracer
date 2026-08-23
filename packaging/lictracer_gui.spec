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
"""
from PyInstaller.utils.hooks import collect_data_files

osadl_datas = collect_data_files("osadl_matrix")

a = Analysis(
    ["..\\src\\ui\\main.py"],
    pathex=[".."],
    binaries=[],
    datas=[
        ("..\\config", "config"),
        ("..\\data\\knowledge_base", "data\\knowledge_base"),
    ]
    + osadl_datas,
    hiddenimports=[
        # tree-sitter 原生扩展与其语言包（.pyd 在包内，需显式声明确保收集）
        "tree_sitter",
        "tree_sitter_python",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",  # 未使用，减小体积
        "unittest",
        "pydoc_data",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    console=False,  # 窗口应用，无控制台
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
