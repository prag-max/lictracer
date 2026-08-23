# -*- coding: utf-8 -*-
"""LicTracer 桌面端主窗口（PySide6）—— 本地离线 · 单窗口审计工作流。

布局：顶部品牌条（图标 + 离线徽标）→ 左侧输入/配置面板（拖拽区 · 文件勾选 ·
参数 · 运行控制）+ 右侧结果区（结论主卡 · 逐文件明细表 · 方法学条 · 导出）。

本地离线承诺：全程无任何网络请求；LLM 摘要保持默认关闭。
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import knowledge_base_path
from src.preprocessor.ast_normalizer import tree_sitter_available
from src.reporting.report_builder import render
from src.ui import icons, theme
from src.ui.scanner import filter_by_text, scan_python_files
from src.ui.summary import aggregate_project
from src.ui.worker import AnalyzeWorker

APP_TITLE = "LicTracer · AI 生成代码许可证合规审计"
OFFLINE_TEXT = "● 本地离线 / 代码不出本机"
LICENSE_OPTIONS = [
    "MIT",
    "BSD-3-Clause",
    "Apache-2.0",
    "GPL-3.0",
    "LGPL-3.0",
    "AGPL-3.0",
    "MPL-2.0",
]
STATUS_COLOR = {
    "INCOMPATIBLE": "#dc2626",
    "NEEDS_REVIEW": "#d97706",
    "COMPATIBLE": "#16a34a",
}
STATUS_ZH = {
    "INCOMPATIBLE": "INCOMPATIBLE 不兼容",
    "NEEDS_REVIEW": "NEEDS_REVIEW 待人工复核",
    "COMPATIBLE": "COMPATIBLE 兼容",
    "UNKNOWN": "UNKNOWN 无有效结果",
}
LEVEL_SHORT = {
    1: "L1 精确相等",
    2: "L2 结构包含",
    3: "L3 锚点游程",
    4: "L4 行级证据",
}
LEVEL_COLOR = {1: "#1d4ed8", 2: "#1d4ed8", 3: "#b45309", 4: "#94a3b8"}


class EvidenceDialog(QDialog):
    """单文件证据链查看器。"""

    def __init__(self, file_name: str, report: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"证据链 —— {file_name}")
        self.resize(780, 540)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        view = QPlainTextEdit(self)
        view.setReadOnly(True)
        view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        view.setPlainText(self._format(file_name, report))
        font = view.font()
        font.setFamily("Consolas")
        font.setPointSize(10)
        view.setFont(font)
        lay.addWidget(view)
        close = QPushButton("关闭")
        close.clicked.connect(self.accept)
        lay.addWidget(close)

    @staticmethod
    def _format(file_name: str, report: dict) -> str:
        lines: list[str] = []
        cr = report.get("compliance_result") or {}
        lines.append(f"文件：{file_name}")
        lines.append(f"结论：{cr.get('status')}    风险等级：{cr.get('risk_level')}")
        lines.append(f"原因：{cr.get('reason')}")
        steps = cr.get("steps") or []
        if steps:
            lines.append("")
            lines.append("── 合规推演步骤 ──")
            for i, s in enumerate(steps, 1):
                lines.append(f"{i}. {s}")
        ev = report.get("evidence") or []
        lines.append("")
        lines.append(f"── 证据明细（{len(ev)} 条）──")
        for e in ev:
            lvl = e.get("verification_level")
            lines.append(
                f"[{LEVEL_SHORT.get(lvl, f'L{lvl}')}] 来源={e.get('file') or e.get('source')}"
                f"  行区间={e.get('lines')}"
                f"  相似度={e.get('similarity')}"
            )
        return "\n".join(lines)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(icons.app_icon())
        self.resize(1240, 820)
        self.setMinimumSize(1020, 680)
        self.setAcceptDrops(True)

        self._folder: Path | None = None
        self._scan_all: list[Path] = []
        self._results: list[dict] = []
        self._worker: AnalyzeWorker | None = None
        self._settings = QSettings("LicTracer", "lictracer")

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header())
        outer.addWidget(self._build_body(), stretch=1)

        self.setStyleSheet(theme.APP_QSS)
        self._restore_settings()

    # ---------- 头部 ----------

    def _build_header(self) -> QWidget:
        bar = QWidget(objectName="headerBar")
        bar.setFixedHeight(58)
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)

        logo = QLabel()
        pm = icons.app_icon().pixmap(30, 30)
        logo.setPixmap(pm)
        logo.setFixedSize(32, 32)
        logo.setScaledContents(True)
        h.addWidget(logo)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        t1 = QLabel("LicTracer", objectName="appTitle")
        t2 = QLabel("AI 生成代码许可证合规审计 · 溯源可复现", objectName="appSub")
        titles.addWidget(t1)
        titles.addWidget(t2)
        h.addLayout(titles)

        h.addStretch(1)
        pill = QLabel(OFFLINE_TEXT, objectName="pillOffline")
        pill.setToolTip("全程在本机完成分析与比对，任何代码与结果均不上传网络")
        h.addWidget(pill)
        return bar

    # ---------- 主体分栏 ----------

    def _build_body(self) -> QSplitter:
        split = QSplitter(Qt.Orientation.Horizontal)
        split.setHandleWidth(1)
        split.setChildrenCollapsible(False)
        split.addWidget(self._build_side_panel())
        split.addWidget(self._build_results_area())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([392, 848])
        self._splitter = split
        return split

    def _section(self, text: str) -> QLabel:
        return QLabel(text, objectName="sectionTitle")

    # ---------- 左侧面板 ----------

    def _build_side_panel(self) -> QWidget:
        panel = QWidget(objectName="sidePanel")
        panel.setMinimumWidth(368)
        panel.setMaximumWidth(460)
        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(9)

        v.addWidget(self._section("① 待审计项目"))
        v.addWidget(self._build_drop_zone())

        tools = QHBoxLayout()
        tools.setSpacing(6)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("筛选路径，如 tests/")
        self.filter_edit.addAction(
            icons.icon("search", theme.TEXT_3), QLineEdit.ActionPosition.LeadingPosition
        )
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self.apply_filter)
        tools.addWidget(self.filter_edit, stretch=1)
        b_all = QPushButton("全选")
        b_none = QPushButton("清除")
        for b in (b_all, b_none):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        b_all.clicked.connect(lambda: self.set_all_checked(True))
        b_none.clicked.connect(lambda: self.set_all_checked(False))
        tools.addWidget(b_all)
        tools.addWidget(b_none)
        v.addLayout(tools)

        self.scan_label = QLabel("已扫描 0 个 .py 文件", objectName="faint")
        v.addWidget(self.scan_label)
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        v.addWidget(self.file_list, stretch=1)

        v.addWidget(self._section("② 审计配置"))
        grid_v = QVBoxLayout()
        grid_v.setSpacing(7)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("项目许可证"))
        self.license_combo = QComboBox()
        self.license_combo.addItems(LICENSE_OPTIONS)
        row1.addWidget(self.license_combo, stretch=1)
        grid_v.addLayout(row1)

        row2 = QHBoxLayout()
        kb_lbl = QLabel("知识库")
        kb_lbl.setToolTip("留空使用随应用内置的默认知识库；高级用户可选自定义目录")
        row2.addWidget(kb_lbl)
        self.kb_edit = QLineEdit()
        self.kb_edit.setPlaceholderText("内置默认（留空）")
        row2.addWidget(self.kb_edit, stretch=1)
        kb_btn = QPushButton("浏览")
        kb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        kb_btn.clicked.connect(self.on_pick_kb)
        row2.addWidget(kb_btn)
        grid_v.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("top_k"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 100)
        self.topk_spin.setValue(10)
        self.topk_spin.setToolTip("溯源召回候选上限")
        row3.addWidget(self.topk_spin)
        row3.addSpacing(10)
        anchor_lbl = QLabel("锚点行数 ≥")
        anchor_lbl.setToolTip(
            "高级项：L3 锚点行游程门槛（min_anchor_lines）。调大更保守，调小反之；默认 3"
        )
        row3.addWidget(anchor_lbl)
        self.anchor_spin = QSpinBox()
        self.anchor_spin.setRange(1, 50)
        self.anchor_spin.setValue(3)
        row3.addWidget(self.anchor_spin)
        row3.addStretch(1)
        grid_v.addLayout(row3)
        v.addLayout(grid_v)

        v.addSpacing(2)
        self.checklist_label = QLabel(
            "就绪。拖入或选择文件夹后将自动校验知识库与清单。", objectName="strip"
        )
        self.checklist_label.setWordWrap(True)
        v.addWidget(self.checklist_label)

        prog_row = QVBoxLayout()
        prog_row.setSpacing(4)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        prog_row.addWidget(self.progress)
        self.progress_label = QLabel("", objectName="faint")
        prog_row.addWidget(self.progress_label)
        v.addLayout(prog_row)

        run_row = QHBoxLayout()
        run_row.setSpacing(8)
        self.run_btn = QPushButton(" 开始审计", objectName="primaryBtn")
        self.run_btn.setIcon(icons.icon("play", "#ffffff"))
        self.run_btn.setFixedHeight(42)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.start_audit)
        run_row.addWidget(self.run_btn, stretch=1)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setIcon(icons.icon("stop", theme.DANGER))
        self.cancel_btn.setObjectName("dangerGhost")
        self.cancel_btn.setFixedHeight(42)
        self.cancel_btn.setFixedWidth(46)
        self.cancel_btn.setToolTip("取消（当前文件完成后停止）")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_audit)
        run_row.addWidget(self.cancel_btn)
        v.addLayout(run_row)
        return panel

    def _build_drop_zone(self) -> QFrame:
        self.drop_zone = QFrame(objectName="dropZone")
        self.drop_zone.setFixedHeight(84)
        self.drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        dz = QVBoxLayout(self.drop_zone)
        dz.setContentsMargins(12, 10, 12, 10)
        dz.setSpacing(3)
        top = QHBoxLayout()
        ic = QLabel()
        ic.setPixmap(icons.icon("folder", theme.ACCENT, 20).pixmap(20, 20))
        top.addWidget(ic)
        self.drop_hint = QLabel("拖入待审计的 AI 项目文件夹，或点击选择")
        self.drop_hint.setStyleSheet(
            f"color:{theme.TEXT_2}; font-size:13px; font-weight:600;"
            "border:none; background:transparent;"
        )
        top.addWidget(self.drop_hint)
        top.addStretch(1)
        dz.addLayout(top)
        self.folder_label = QLabel("未选择文件夹", objectName="faint")
        self.folder_label.setStyleSheet("border:none; background:transparent;")
        dz.addWidget(self.folder_label)
        return self.drop_zone

    # ---------- 右侧结果区 ----------

    def _build_results_area(self) -> QWidget:
        holder = QWidget()
        v = QVBoxLayout(holder)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(11)

        self.pages = QStackedWidget()

        empty = QWidget()
        ev = QVBoxLayout(empty)
        ev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shield = QLabel()
        shield.setPixmap(icons.icon("shield", "#c3cfdd", 72).pixmap(72, 72))
        shield.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ev.addWidget(shield)
        t = QLabel("开始你的第一次审计", objectName="muted")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size:15px; font-weight:600;")
        ev.addWidget(t)
        s = QLabel(
            "左侧拖入项目文件夹 → 勾选文件 → 点击「开始审计」\n结论、证据链与方法学状态将展示在这里",
            objectName="faint",
        )
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ev.addWidget(s)

        results = QWidget()
        rv = QVBoxLayout(results)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(11)
        rv.addWidget(self._build_verdict_card())
        rv.addWidget(self._build_table(), stretch=1)
        self.methodology_label = QLabel("方法学透明条：待审计后展示。", objectName="methodBar")
        self.methodology_label.setWordWrap(True)
        rv.addWidget(self.methodology_label)
        rv.addLayout(self._build_export_row())

        self.pages.addWidget(empty)
        self.pages.addWidget(results)
        v.addWidget(self.pages)
        return holder

    def _build_verdict_card(self) -> QFrame:
        self.verdict_card = QFrame(objectName="verdictCard")
        self.verdict_card.setProperty("status", "UNKNOWN")
        self.verdict_card.setFixedHeight(96)
        h = QHBoxLayout(self.verdict_card)
        h.setContentsMargins(20, 12, 20, 12)
        left = QVBoxLayout()
        left.setSpacing(2)
        self.card_title = QLabel("尚未审计", objectName="heroStatus")
        self.card_sub = QLabel(
            "导入文件夹并运行审计后，这里显示项目级合规结论", objectName="heroMeta"
        )
        left.addWidget(self.card_title)
        left.addWidget(self.card_sub)
        h.addLayout(left)
        h.addStretch(1)
        self.card_detail = QLabel("", objectName="heroMeta")
        self.card_detail.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        h.addWidget(self.card_detail)
        return self.verdict_card

    def _build_table(self) -> QTreeWidget:
        cols = [
            "文件 / 片段", "行号", "来源", "许可证", "相似度",
            "级别", "证据", "驱动", "归属",
        ]
        self.table = QTreeWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHeaderLabels(cols)
        header = self.table.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 236)
        for c in range(1, len(cols)):
            header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.table.itemDoubleClicked.connect(self.open_evidence)
        return self.table

    def _build_export_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.export_status = QLabel("", objectName="faint")
        row.addWidget(self.export_status, stretch=1)
        self.export_md_btn = QPushButton("导出 Markdown")
        self.export_html_btn = QPushButton("导出 HTML")
        for b in (self.export_md_btn, self.export_html_btn):
            b.setIcon(icons.icon("export", theme.TEXT_2))
            b.setEnabled(False)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            row.addWidget(b)
        self.export_md_btn.clicked.connect(lambda: self.export_report("markdown"))
        self.export_html_btn.clicked.connect(lambda: self.export_report("html"))
        return row

    # ---------- 输入：拖拽 / 选择 ----------

    def _set_drag_over(self, over: bool) -> None:
        self.drop_zone.setProperty("dragOver", "true" if over else "false")
        self.drop_zone.style().unpolish(self.drop_zone)
        self.drop_zone.style().polish(self.drop_zone)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_drag_over(True)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        self._set_drag_over(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drag_over(False)
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                self.set_folder(p)
                break

    def mousePressEvent(self, event) -> None:  # dropzone 点击 = 选择文件夹
        widget = self.childAt(event.position().toPoint())
        if widget is not None and (
            widget is self.drop_zone or self.drop_zone.isAncestorOf(widget)
        ):
            self.on_pick_folder()
        super().mousePressEvent(event)

    def on_pick_folder(self) -> None:
        start = str(self._folder) if self._folder else str(Path.home())
        d = QFileDialog.getExistingDirectory(self, "选择待审计的项目文件夹", start)
        if d:
            self.set_folder(Path(d))

    def set_folder(self, folder: Path) -> None:
        self._folder = folder
        self.folder_label.setText(str(folder))
        self.rescan()

    def rescan(self) -> None:
        if not self._folder:
            return
        self._scan_all = scan_python_files(self._folder)
        self.scan_label.setText(f"已扫描 {len(self._scan_all)} 个 .py 文件")
        self.file_list.clear()
        for p in self._scan_all:
            try:
                shown = str(p.relative_to(self._folder))
            except ValueError:
                shown = str(p)
            item = QListWidgetItem(shown)
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setToolTip(str(p))
            self.file_list.addItem(item)
        self.apply_filter()

    def apply_filter(self) -> None:
        q = self.filter_edit.text()
        visible = {str(p) for p in filter_by_text(self._scan_all, q)}
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            item.setHidden(str(path) not in visible)

    def set_all_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def selected_files(self) -> list[Path]:
        out = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.CheckState.Checked and not item.isHidden():
                out.append(Path(item.data(Qt.ItemDataRole.UserRole)))
        return out

    def on_pick_kb(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "选择自定义知识库目录（含 licenses.json 的 KB 根）"
        )
        if d:
            self.kb_edit.setText(d)

    # ---------- 校验清单 ----------

    def precheck(self, files: list[Path]) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warns: list[str] = []
        kb_raw = self.kb_edit.text().strip()
        kb = Path(kb_raw) if kb_raw else knowledge_base_path()
        if not kb.is_dir():
            errors.append(f"✗ 知识库不存在：{kb}")
        elif not (kb / "licenses.json").exists():
            warns.append(f"⚠ KB 缺少 licenses.json（来源按 UNKNOWN 处理）：{kb}")
        if len(files) == 0:
            errors.append("✗ 未勾选任何 .py 文件")
        else:
            empty = [p.name for p in files[:50] if p.stat().st_size == 0]
            if empty:
                warns.append(f"⚠ 存在空文件 {len(empty)} 个，如：{empty[:3]}")
        warns.append(
            "✓ tree-sitter 可用"
            if tree_sitter_available()
            else "⚠ tree-sitter 不可用，预处理降级为正则（报告将显式标注）"
        )
        warns.append("✓ 内置默认知识库" if not kb_raw else f"ℹ 自定义知识库：{kb}")
        return errors, warns

    def postcheck(self, agg: dict) -> list[str]:
        notes: list[str] = []
        n_err = len(agg["errors"])
        notes.append(
            f"⚠ {n_err} 个文件解析失败未计入结论，如 {[e['path'] for e in agg['errors'][:3]]}"
            if n_err
            else "✓ 全部选中文件解析成功"
        )
        notes.append(
            f"⚠ {len(agg['ambiguous'])} 个文件存在归属歧义（已标注 ⚠，建议人工复核）"
            if agg["ambiguous"]
            else "✓ 无归属歧义"
        )
        return notes

    # ---------- 运行 ----------

    def start_audit(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        files = self.selected_files()
        errors, warns = self.precheck(files)
        if errors:
            msg = "　".join(warns + errors)
            self.checklist_label.setText(msg)
            self.checklist_label.setStyleSheet(
                f"background:#fef2f2;border:1px solid #fecaca;border-radius:8px;"
                f"padding:7px 10px;color:{theme.DANGER};font-size:12px;"
            )
            return
        self.checklist_label.setText("　".join(warns))
        self.checklist_label.setStyleSheet("")

        project_license = self.license_combo.currentText()
        top_k = self.topk_spin.value()
        anchor = self.anchor_spin.value()
        kb_raw = self.kb_edit.text().strip()
        self._persist_settings(project_license, top_k, anchor)

        self._worker = AnalyzeWorker(
            files,
            project_license=project_license,
            top_k=top_k,
            kb_path=kb_raw or None,
            min_anchor_lines=anchor,
        )
        self._worker.progress.connect(self.on_progress)
        self._worker.batch_done.connect(self.on_batch_done)
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, max(1, len(files)))
        self.progress.setValue(0)
        self.progress_label.setText("")
        self.export_status.setText("")
        self._worker.start()

    def cancel_audit(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.progress_label.setText("取消中（当前文件完成后停止）…")

    def on_progress(self, done: int, total: int, name: str) -> None:
        self.progress.setValue(done)
        cur = f"当前：{name}" if name else ""
        self.progress_label.setText(f"已处理 {done}/{total}　{cur}")

    def on_batch_done(self, entries: list[dict]) -> None:
        self._results = entries
        cancelled = bool(self._worker and self._worker.cancelled)
        self._worker = None
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        agg = aggregate_project(entries)
        self.render_summary(agg, entries)
        prefix = "【已取消】" if cancelled else ""
        self.checklist_label.setText(prefix + "　".join(self.postcheck(agg)))
        for b in (self.export_md_btn, self.export_html_btn):
            b.setEnabled(bool(entries))
        self.pages.setCurrentIndex(1 if entries else 0)

    # ---------- 结果渲染 ----------

    def render_summary(self, agg: dict, entries: list[dict]) -> None:
        status = agg["status"]
        self.verdict_card.setProperty("status", status)
        self.verdict_card.style().unpolish(self.verdict_card)
        self.verdict_card.style().polish(self.verdict_card)
        c = agg["counts"]
        n_amb = len(agg["ambiguous"])
        self.card_title.setText(f"项目级结论：{STATUS_ZH[status]}")
        self.card_sub.setText(
            f"风险等级 {agg['risk_level']}　·　成功 {agg['analyzed']}/{agg['total']} 文件"
        )
        amb_txt = f"　<span style='color:#fef08a'>歧义 {n_amb}</span>" if n_amb else ""
        self.card_detail.setText(
            f"<span>红 <b>{c['INCOMPATIBLE']}</b>　黄 <b>{c['NEEDS_REVIEW']}</b>"
            f"　绿 <b>{c['COMPATIBLE']}</b>　命中片段文件 <b>{agg['hit_files']}</b>{amb_txt}</span>"
        )
        self.fill_table(entries)
        self.render_methodology(agg)

    def fill_table(self, entries: list[dict]) -> None:
        self.table.clear()
        for e in entries:
            path = Path(e["path"])
            rep = e.get("report")
            top = QTreeWidgetItem([path.name] + [""] * 8)
            top.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "report": rep})
            top.setFirstColumnSpanned(True)
            if rep is None:
                top.setText(0, f"✗ 解析失败：{path.name}　({str(e.get('error', ''))[:120]})")
                top.setForeground(0, QBrush(QColor(theme.DANGER)))
                self.table.addTopLevelItem(top)
                continue
            cr = rep.get("compliance_result") or {}
            st = cr.get("status") or "UNKNOWN"
            attr = rep.get("attribution") or {}
            amb = "⚠ 归属存在歧义，建议人工复核" if attr.get("attribution_ambiguous") else ""
            top.setText(0, f"● {path.name}")
            top.setForeground(0, QBrush(QColor(STATUS_COLOR.get(st, "#64748b"))))
            segs = rep.get("segments") or []
            top.setText(2, f"{st.split()[0]}｜{len(segs)} 片段")
            top.setForeground(2, QBrush(QColor(theme.TEXT_2)))
            top.setText(8, amb)
            if amb:
                top.setForeground(8, QBrush(QColor("#e65100")))
            self.table.addTopLevelItem(top)
            for s in segs:
                lvl = s.get("verification_level")
                child = QTreeWidgetItem(
                    [
                        f"片段 #{s.get('id')}",
                        str(s.get("lines") or ""),
                        str(s.get("source") or ""),
                        str(s.get("license") or ""),
                        f"{s.get('similarity'):.3f}"
                        if isinstance(s.get("similarity"), (int, float))
                        else "",
                        LEVEL_SHORT.get(lvl, f"L{lvl}"),
                        "✓" if s.get("is_primary") else "",
                        "✓" if s.get("drives_conclusion") else "",
                    ]
                )
                child.setData(
                    0, Qt.ItemDataRole.UserRole, {"path": str(path), "report": rep}
                )
                child.setForeground(5, QBrush(QColor(LEVEL_COLOR.get(lvl, "#64748b"))))
                top.addChild(child)
        self.table.expandAll()

    def render_methodology(self, agg: dict) -> None:
        ms = agg["methodologies"]
        if not ms:
            self.methodology_label.setText("方法学透明条：无可用数据。")
            return
        ts = sorted({m.get("tree_sitter", "?") for m in ms})
        modes = sorted({str(m.get("retriever_mode", "?")) for m in ms})
        kbs = sorted({m.get("kb_files") for m in ms}, key=lambda x: (x is None, x))
        anchors = sorted(
            {m.get("verification_min_anchor_lines") for m in ms},
            key=lambda x: (x is None, x),
        )
        degrade = "" if ts == ["available"] else "　<b>⚠ 正则降级！</b>"
        self.methodology_label.setTextFormat(Qt.TextFormat.RichText)
        self.methodology_label.setText(
            f"<b>方法学透明</b>　tree_sitter: {'/'.join(ts)}{degrade}"
            f"　|　检索模式: {'/'.join(modes)}"
            f"　|　KB 文件数: {kbs}"
            f"　|　锚点门槛: {anchors}"
            "　|　相似度为 MinHash 估计值仅作排序展示；克隆裁决由确定性验证器完成"
        )

    def open_evidence(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("report") is None:
            return
        dlg = EvidenceDialog(Path(data["path"]).name, data["report"], self)
        dlg.exec()

    # ---------- 导出 ----------

    def export_report(self, fmt: str) -> None:
        if not self._results:
            return
        ext = "md" if fmt == "markdown" else "html"
        default = str(Path.home() / f"lictracer_report.{ext}")
        fname, _ = QFileDialog.getSaveFileName(self, "导出审计报告", default, f"*.{ext}")
        if not fname:
            return
        agg = aggregate_project(self._results)
        title = "LicTracer 项目许可证合规审计报告"
        parts: list[str] = []
        if fmt == "markdown":
            head = [
                f"# {title}",
                "",
                "- 形态：本地离线桌面端（代码不出本机）",
                f"- 审计文件：{agg['analyzed']}/{agg['total']} 成功；命中片段文件 {agg['hit_files']}",
                f"- **项目级结论：{agg['status']}（风险 {agg['risk_level']}）**",
                f"- 红 {agg['counts']['INCOMPATIBLE']} ／ 黄 {agg['counts']['NEEDS_REVIEW']}"
                f" ／ 绿 {agg['counts']['COMPATIBLE']}",
                "",
            ]
            parts.append("\n".join(head))
            for e in self._results:
                if e.get("report") is None:
                    parts.append(f"## {e['path']}\n\n- ✗ 解析失败：{e.get('error')}\n")
                else:
                    parts.append(f"## {e['path']}\n\n" + render(e["report"], "markdown"))
            text = "\n\n---\n\n".join(parts) + "\n"
        else:
            sections = []
            for e in self._results:
                inner = (
                    render(e["report"], "html")
                    if e.get("report")
                    else f"<p>✗ 解析失败：{e.get('error')}</p>"
                )
                body = inner.split("<body>", 1)[-1].split("</body>", 1)[0]
                sections.append(
                    f"<section><h2 style='border-top:2px solid #ccc;padding-top:8px'>"
                    f"{e['path']}</h2>{body}</section>"
                )
            color = STATUS_COLOR.get(agg["status"], "#64748b")
            text = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{title}</title></head><body>"
                f"<h1>{title}</h1>"
                f"<p>项目级结论：<b style='color:{color}'>{agg['status']}</b>"
                f"（风险 {agg['risk_level']}）；成功 {agg['analyzed']}/{agg['total']}；"
                f"红 {agg['counts']['INCOMPATIBLE']} ／ 黄 {agg['counts']['NEEDS_REVIEW']}"
                f" ／ 绿 {agg['counts']['COMPATIBLE']}</p>"
                + "".join(sections)
                + "</body></html>"
            )
        Path(fname).write_text(text, encoding="utf-8")
        self.export_status.setText(f"已导出：{fname}")

    # ---------- 设置记忆 ----------

    def _restore_settings(self) -> None:
        s = self._settings
        folder = s.value("last_folder", "", type=str)
        if folder and Path(folder).is_dir():
            self.set_folder(Path(folder))
        lic = s.value("project_license", "MIT", type=str)
        if lic in LICENSE_OPTIONS:
            self.license_combo.setCurrentText(lic)
        self.topk_spin.setValue(s.value("top_k", 10, type=int))
        self.anchor_spin.setValue(s.value("min_anchor_lines", 3, type=int))
        self.kb_edit.setText(s.value("kb_override", "", type=str))
        geo = s.value("win_geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        state = s.value("splitter_state")
        if state is not None:
            self._splitter.restoreState(state)

    def _persist_settings(self, license_: str, top_k: int, anchor: int) -> None:
        s = self._settings
        if self._folder:
            s.setValue("last_folder", str(self._folder))
        s.setValue("project_license", license_)
        s.setValue("top_k", top_k)
        s.setValue("min_anchor_lines", anchor)
        s.setValue("kb_override", self.kb_edit.text().strip())

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt 命名)
        s = self._settings
        s.setValue("win_geometry", self.saveGeometry())
        try:
            s.setValue("splitter_state", self._splitter.saveState())
        except RuntimeError:
            pass
        super().closeEvent(event)


def _run_selfcheck() -> int:
    """frozen 环境自检：端到端验证打包产物内的完整分析链路。"""
    lines: list[str] = []
    code = 0
    try:
        from src.pipeline import analyze_text

        rep = analyze_text(
            "import os\n\n\ndef calc(a, b):\n    total = a + b\n    return total\n"
        )
        m = rep.get("methodology") or {}
        cr = rep.get("compliance_result") or {}
        lines.append("SELFCHECK OK")
        lines.append(f"tree_sitter = {m.get('tree_sitter')}")
        lines.append(f"retriever_mode = {m.get('retriever_mode')}")
        lines.append(f"kb_files = {m.get('kb_files')}")
        lines.append(f"anchor = {m.get('verification_min_anchor_lines')}")
        lines.append(f"status = {cr.get('status')} risk = {cr.get('risk_level')}")
    except Exception:
        code = 1
        lines.append("SELFCHECK FAILED")
        lines.append(traceback.format_exc())

    out_name = "selfcheck_result.txt"
    if getattr(sys, "frozen", False):
        out_path = Path(sys.executable).resolve().parent / out_name
    else:
        out_path = Path.cwd() / out_name
    try:
        out_path.write_text("\n".join(lines), encoding="utf-8")
    except OSError:
        pass
    print("\n".join(lines))
    return code


def main() -> int:
    if "--selfcheck" in sys.argv[1:]:
        return _run_selfcheck()
    app = QApplication(sys.argv)
    app.setApplicationName("LicTracer")
    app.setOrganizationName("LicTracer")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setWindowIcon(icons.app_icon())
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
