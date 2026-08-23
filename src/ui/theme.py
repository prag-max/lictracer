# -*- coding: utf-8 -*-
"""桌面端视觉设计系统：色板令牌 + 字阶 + 统一 QSS。

风格基调：专业审计工具的浅色体系 —— 冷灰画布、白色卡片、蓝色主行动色，
红黄绿仅用于合规结论语义。所有控件统一圆角与留白节奏。
"""
from __future__ import annotations

# ---------- 设计令牌 ----------
CANVAS = "#eef2f7"        # 窗口画布
SURFACE = "#ffffff"       # 卡片/面板
SURFACE_ALT = "#f8fafc"   # 次级表面（表头、条带）
BORDER = "#dfe6ee"        # 描边
TEXT = "#0f172a"          # 主文本
TEXT_2 = "#475569"        # 次级文本
TEXT_3 = "#94a3b8"        # 弱文本/占位
ACCENT = "#2563eb"        # 主行动色
ACCENT_HOVER = "#1d4ed8"
ACCENT_SUBTLE = "#eff6ff"
DANGER = "#dc2626"
WARN = "#d97706"
OK = "#16a34a"

FONT_FAMILY = '"Microsoft YaHei UI", "Segoe UI", sans-serif'

APP_QSS = f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {TEXT};
}}
QMainWindow, QDialog {{ background: {CANVAS}; }}

/* ---------- 面板与卡片 ---------- */
#sidePanel {{
    background: {SURFACE};
    border-right: 1px solid {BORDER};
}}
#headerBar {{
    background: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}
QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

/* 结论主卡：颜色由动态属性 status 驱动 */
#verdictCard {{
    border-radius: 12px;
    border: none;
    background: {SURFACE_ALT};
}}
#verdictCard[status="INCOMPATIBLE"] {{ background: {DANGER}; }}
#verdictCard[status="NEEDS_REVIEW"] {{ background: #b45309; }}
#verdictCard[status="COMPATIBLE"]   {{ background: {OK}; }}
#verdictCard[status="UNKNOWN"]      {{ background: #64748b; }}
#verdictCard QLabel {{ color: #ffffff; }}

/* ---------- 文本层级 ---------- */
QLabel#appTitle   {{ font-size: 16px; font-weight: 700; }}
QLabel#appSub     {{ font-size: 11px; color: {TEXT_2}; }}
QLabel#sectionTitle {{ font-size: 12px; font-weight: 700; color: {TEXT_2};
                       letter-spacing: 1px; }}
QLabel#muted      {{ color: {TEXT_2}; font-size: 12px; }}
QLabel#faint      {{ color: {TEXT_3}; font-size: 11px; }}
QLabel#heroStatus {{ font-size: 22px; font-weight: 800; }}
QLabel#heroMeta   {{ font-size: 12px; }}
QLabel#pillOffline {{
    color: {OK}; border: 1px solid {OK}; border-radius: 11px;
    padding: 3px 12px; font-size: 12px; font-weight: 600; background: #f0fdf4;
}}
QLabel#strip {{
    background: {SURFACE_ALT}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 7px 10px; color: {TEXT_2}; font-size: 12px;
}}
QLabel#methodBar {{
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 8px; padding: 6px 10px; color: #14532d; font-size: 11px;
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QComboBox, QSpinBox {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 5px 9px;
    min-height: 24px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {ACCENT};
}}
QLineEdit::placeholder {{ color: {TEXT_3}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; border: 1px solid {BORDER};
    selection-background-color: {ACCENT_SUBTLE}; selection-color: {TEXT};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {SURFACE_ALT}; border: none; width: 18px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {ACCENT_SUBTLE}; }}
QPushButton[iconic="true"] {{ padding: 5px 7px; }}

/* ---------- 按钮 ---------- */
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 6px 14px;
    font-weight: 600;
}}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:pressed {{ background: {ACCENT_SUBTLE}; }}
QPushButton:disabled {{ color: {TEXT_3}; border-color: {BORDER}; background: {SURFACE_ALT}; }}
QPushButton#primaryBtn {{
    background: {ACCENT}; border: none; color: #ffffff;
    padding: 10px 16px; font-size: 14px; font-weight: 700;
}}
QPushButton#primaryBtn:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primaryBtn:pressed {{ background: #173db3; }}
QPushButton#primaryBtn:disabled {{ background: #b9cdf5; color: #f2f6ff; }}
QPushButton#dangerGhost {{
    color: {DANGER}; border-color: #fecaca; background: #ffffff;
}}
QPushButton#dangerGhost:hover {{ background: #fef2f2; }}

/* ---------- 列表 / 表格 ---------- */
QListWidget, QTreeWidget {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 9px;
    padding: 4px;
    outline: none;
    alternate-background-color: {SURFACE_ALT};
}}
QListWidget::item, QTreeWidget::item {{
    padding: 4px 6px; border-radius: 5px;
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {ACCENT_SUBTLE}; color: {TEXT};
}}
QHeaderView::section {{
    background: {SURFACE_ALT};
    color: {TEXT_2};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 7px 8px;
    font-size: 12px; font-weight: 600;
}}
QTreeWidget::branch {{ background: transparent; }}

/* ---------- 进度条 ---------- */
QProgressBar {{
    background: {SURFACE_ALT}; border: 1px solid {BORDER};
    border-radius: 8px; height: 16px; text-align: center;
    font-size: 10px; color: {TEXT_2};
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 7px; }}

/* ---------- 分割器 ---------- */
QSplitter::handle {{ background: {BORDER}; width: 1px; }}
QSplitter::handle:hover {{ background: {ACCENT}; }}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #cbd5e1; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_3}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #cbd5e1; border-radius: 4px; min-width: 30px; }}

/* ---------- 拖拽区（dragOver 动态属性高亮） ---------- */
#dropZone {{
    border: 2px dashed {BORDER}; border-radius: 10px; background: {SURFACE_ALT};
}}
#dropZone[dragOver="true"] {{
    border: 2px dashed {ACCENT}; background: {ACCENT_SUBTLE};
}}
"""
