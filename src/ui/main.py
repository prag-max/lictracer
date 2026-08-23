# -*- coding: utf-8 -*-
"""LicTracer 桌面端主窗口（PySide6）。

单窗口工作流：输入（拖拽/选择文件夹）→ 筛选勾选 → 配置 → 一键批处理审计
→ 项目级结论卡片 + 逐文件明细表（证据链展开 / 归属歧义标注）→ 导出。

本地离线承诺：全程无任何网络请求；LLM 摘要保持默认关闭；
窗口显著位置常驻「本地离线 / 代码不出本机」标识。
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QBrush, QColor, QDragEnterEvent, QDropEvent
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
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import knowledge_base_path
from src.preprocessor.ast_normalizer import tree_sitter_available
from src.reporting.report_builder import render
from src.ui.scanner import filter_by_text, scan_python_files
from src.ui.summary import aggregate_project
from src.ui.worker import AnalyzeWorker

APP_TITLE = "LicTracer · AI 生成代码许可证合规审计"
OFFLINE_BADGE = "本地离线 / 代码不出本机"
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
    "INCOMPATIBLE": "#c62828",  # 红
    "NEEDS_REVIEW": "#f9a825",  # 黄
    "COMPATIBLE": "#2e7d32",  # 绿
}
STATUS_TEXT_COLOR = {"INCOMPATIBLE": "#fff", "NEEDS_REVIEW": "#1a1a1a", "COMPATIBLE": "#fff"}
LEVEL_NAME = {
    1: "L1 规范型精确相等",
    2: "L2 结构序列包含",
    3: "L3 锚点行游程",
    4: "L4 行级证据",
}

_CARD_QSS = """
#resultCard[status="INCOMPATIBLE"] { background: #c62828; }
#resultCard[status="NEEDS_REVIEW"] { background: #f9a825; }
#resultCard[status="COMPATIBLE"]   { background: #2e7d32; }
#resultCard[status="UNKNOWN"]      { background: #616161; }
#resultCard { border-radius: 8px; }
#resultCard QLabel { color: white; font-size: 14px; }
#resultCard QLabel#cardTitle { color: white; font-size: 20px; font-weight: 700; }
#resultCard[status="NEEDS_REVIEW"] QLabel { color: #1a1a1a; }
#resultCard[status="NEEDS_REVIEW"] QLabel#cardTitle { color: #1a1a1a; }
"""


class EvidenceDialog(QDialog):
    """单文件证据链查看器：redup 行级证据 + 合规推演步骤。"""

    def __init__(self, file_name: str, report: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"证据链 —— {file_name}")
        self.resize(760, 520)
        lay = QVBoxLayout(self)
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
            lvl_txt = LEVEL_NAME.get(lvl, f"L{lvl}")
            lines.append(
                f"[{lvl_txt}] 来源={e.get('file') or e.get('source')}"
                f"  行区间={e.get('lines')}"
                f"  相似度={e.get('similarity')}"
                f"  命中行数={len(e.get('matched_lines') or [])}"
            )
        return "\n".join(lines)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE}　【{OFFLINE_BADGE}】")
        self.resize(1080, 760)
        self.setMinimumSize(940, 660)
        self.setAcceptDrops(True)

        self._folder: Path | None = None
        self._scan_all: list[Path] = []
        self._results: list[dict] = []
        self._worker: AnalyzeWorker | None = None
        self._settings = QSettings("LicTracer", "lictracer")

        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setSpacing(8)

        lay.addWidget(self._build_drop_zone())
        lay.addWidget(self._build_file_section())
        lay.addWidget(self._build_config_section())
        lay.addWidget(self._build_run_section())
        lay.addWidget(self._build_checklist_bar())
        lay.addWidget(self._build_result_card(), stretch=0)
        lay.addWidget(self._build_result_table(), stretch=1)
        lay.addWidget(self._build_methodology_bar())
        lay.addWidget(self._build_export_row())

        self.setStyleSheet(_CARD_QSS)
        self._restore_settings()

    # ---------- UI 构建 ----------

    def _build_drop_zone(self) -> QFrame:
        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("dropZone")
        self.drop_zone.setFixedHeight(72)
        self.drop_zone.setStyleSheet(
            "#dropZone { border: 2px dashed #90a4ae; border-radius: 8px; background: #fafafa; }"
            "#dropZone:hover { border-color: #1976d2; background: #eef6fd; }"
        )
        dz_lay = QHBoxLayout(self.drop_zone)
        hint = QLabel("把「待审计的 AI 项目文件夹」拖到这里，或点击选择文件夹")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#546e7a; font-size:14px; border:none;")
        dz_lay.addWidget(hint)
        browse = QPushButton("选择文件夹…")
        browse.clicked.connect(self.on_pick_folder)
        dz_lay.addWidget(browse)
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setStyleSheet("color:#37474f; border:none; font-weight:600;")
        dz_lay.addWidget(self.folder_label)
        return self.drop_zone

    def _build_file_section(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        self.scan_label = QLabel("已扫描 0 个 .py 文件")
        bar.addWidget(self.scan_label)
        bar.addStretch(1)
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("按路径/名称筛选，如 tests/ 或 _v2")
        self.filter_edit.setMaximumWidth(280)
        self.filter_edit.textChanged.connect(self.apply_filter)
        bar.addWidget(self.filter_edit)
        btn_all = QPushButton("全选")
        btn_none = QPushButton("全不选")
        btn_all.clicked.connect(lambda: self.set_all_checked(True))
        btn_none.clicked.connect(lambda: self.set_all_checked(False))
        bar.addWidget(btn_all)
        bar.addWidget(btn_none)

        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        v.addLayout(bar)
        v.addWidget(self.file_list, stretch=0)
        self.file_list.setFixedHeight(170)
        return w

    def _build_config_section(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel("项目整体许可证"))
        self.license_combo = QComboBox()
        self.license_combo.addItems(LICENSE_OPTIONS)
        h.addWidget(self.license_combo)

        h.addWidget(QLabel("知识库路径"))
        self.kb_edit = QLineEdit()
        self.kb_edit.setPlaceholderText("留空使用内置默认知识库")
        h.addWidget(self.kb_edit, stretch=2)
        kb_btn = QPushButton("浏览…")
        kb_btn.setToolTip("自定义知识库路径（高级）：留空即用随应用分发的默认知识库")
        kb_btn.clicked.connect(self.on_pick_kb)
        h.addWidget(kb_btn)

        h.addWidget(QLabel("top_k"))
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 100)
        self.topk_spin.setValue(10)
        self.topk_spin.setToolTip("溯源召回候选上限")
        h.addWidget(self.topk_spin)

        h.addWidget(QLabel("锚点行数≥"))
        self.anchor_spin = QSpinBox()
        self.anchor_spin.setRange(1, 50)
        self.anchor_spin.setValue(3)
        self.anchor_spin.setToolTip(
            "高级项：L3 锚点行游程门槛（min_anchor_lines）。"
            "调大更保守（漏检↑误报↓），调小反之；默认 3 与 CLI/settings.yaml 口径一致"
        )
        h.addWidget(self.anchor_spin)
        return w

    def _build_run_section(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        self.run_btn = QPushButton("▶ 开始审计")
        self.run_btn.setFixedHeight(38)
        self.run_btn.setStyleSheet(
            "background:#1976d2; color:white; font-weight:700; font-size:15px;"
            "border-radius:6px; padding:0 28px;"
        )
        self.run_btn.clicked.connect(self.start_audit)
        h.addWidget(self.run_btn)

        self.cancel_btn = QPushButton("■ 取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_audit)
        h.addWidget(self.cancel_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setValue(0)
        h.addWidget(self.progress, stretch=1)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color:#546e7a;")
        h.addWidget(self.progress_label, stretch=1)
        return w

    def _build_checklist_bar(self) -> QLabel:
        self.checklist_label = QLabel("就绪。选择文件夹后自动校验知识库与文件清单。")
        self.checklist_label.setWordWrap(True)
        self.checklist_label.setStyleSheet(
            "background:#eceff1; border-radius:6px; padding:6px 10px; color:#37474f;"
        )
        return self.checklist_label

    def _build_result_card(self) -> QFrame:
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setProperty("status", "UNKNOWN")
        self.result_card.setFixedHeight(86)
        h = QHBoxLayout(self.result_card)
        self.card_title = QLabel("尚未审计")
        self.card_title.setObjectName("cardTitle")
        h.addWidget(self.card_title)
        h.addStretch(1)
        self.card_detail = QLabel("项目级结论将在此汇总：状态 / 风险等级 / 命中统计")
        self.card_detail.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(self.card_detail)
        return self.result_card

    def _build_result_table(self) -> QTreeWidget:
        cols = ["文件 / 片段", "行号", "来源", "许可证", "相似度", "验证级别", "主证据", "驱动结论", "归属"]
        self.table = QTreeWidget()
        self.table.setColumnCount(len(cols))
        self.table.setHeaderLabels(cols)
        header = self.table.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 320)
        for c in range(1, len(cols)):
            header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.itemDoubleClicked.connect(self.open_evidence)
        return self.table

    def _build_methodology_bar(self) -> QLabel:
        self.methodology_label = QLabel(
            "方法学透明条：待审计后展示 methodology（tree-sitter 可用性 / 检索模式 / KB 文件数 / 锚点行数）。"
        )
        self.methodology_label.setWordWrap(True)
        self.methodology_label.setStyleSheet(
            "background:#f1f8e9; border-radius:6px; padding:6px 10px; color:#33691e; font-size:12px;"
        )
        return self.methodology_label

    def _build_export_row(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        self.export_md_btn = QPushButton("导出 Markdown")
        self.export_html_btn = QPushButton("导出 HTML")
        self.export_md_btn.clicked.connect(lambda: self.export_report("markdown"))
        self.export_html_btn.clicked.connect(lambda: self.export_report("html"))
        for b in (self.export_md_btn, self.export_html_btn):
            b.setEnabled(False)
            h.addWidget(b)
        h.addStretch(1)
        self.export_status = QLabel("")
        self.export_status.setStyleSheet("color:#546e7a;")
        h.addWidget(self.export_status)
        return w

    # ---------- 输入：拖拽 / 选择 ----------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.is_dir():
                self.set_folder(p)
                break

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
        d = QFileDialog.getExistingDirectory(self, "选择自定义知识库目录（含 licenses.json 的 KB 根）")
        if d:
            self.kb_edit.setText(d)

    # ---------- 校验清单 ----------

    def precheck(self, files: list[Path]) -> tuple[list[str], list[str]]:
        """返回 (致命错误列表, 提示列表)。"""
        errors: list[str] = []
        warns: list[str] = []

        kb_raw = self.kb_edit.text().strip()
        kb = Path(kb_raw) if kb_raw else knowledge_base_path()
        if not kb.is_dir():
            errors.append(f"✗ 知识库不存在：{kb}")
        elif not (kb / "licenses.json").exists():
            warns.append(f"⚠ 知识库缺少 licenses.json（来源许可证映射将按 UNKNOWN 处理并告警）：{kb}")

        empty = [str(p) for p in files[:20] if p.stat().st_size == 0]
        if len(files) == 0:
            errors.append("✗ 未勾选任何 .py 文件")
        elif empty:
            warns.append(f"⚠ 存在空文件 {len(empty)} 个（将被跳过分析或产生空报告），如：{empty[:3]}")

        if not tree_sitter_available():
            warns.append("⚠ tree-sitter 不可用，预处理降级为正则规范化（报告中 methodology 将显式标注）")
        else:
            warns.append("✓ tree-sitter 预处理可用")

        if kb_raw:
            warns.append(f"ℹ 使用自定义知识库：{kb}")
        else:
            warns.append("✓ 使用内置默认知识库（随应用分发）")
        return errors, warns

    def postcheck(self, agg: dict) -> list[str]:
        notes: list[str] = []
        n_err = agg["errors"].__len__()
        if n_err:
            examples = [e["path"] for e in agg["errors"][:3]]
            notes.append(f"⚠ {n_err} 个文件解析失败未计入结论，如：{examples}")
        else:
            notes.append("✓ 全部选中文件均成功解析")
        if agg["ambiguous"]:
            notes.append(
                f"⚠ {len(agg['ambiguous'])} 个文件存在归属歧义（已在明细表标注 ⚠，建议人工复核）"
            )
        else:
            notes.append("✓ 无归属歧义")
        return notes

    # ---------- 运行 ----------

    def start_audit(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        files = self.selected_files()
        errors, warns = self.precheck(files)
        fatal = "　".join(errors) if errors else ""
        self.checklist_label.setText(("　".join(warns) if warns else "") + ("　|　" + fatal if fatal else ""))
        if errors:
            self.checklist_label.setStyleSheet(
                "background:#fbe9e7; border-radius:6px; padding:6px 10px; color:#b71c1c;"
            )
            return
        self.checklist_label.setStyleSheet(
            "background:#eceff1; border-radius:6px; padding:6px 10px; color:#37474f;"
        )

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
        post = self.postcheck(agg)
        prefix = "【已取消】" if cancelled else ""
        self.checklist_label.setText(prefix + "　".join(post))
        for b in (self.export_md_btn, self.export_html_btn):
            b.setEnabled(bool(entries))

    # ---------- 结果渲染 ----------

    def render_summary(self, agg: dict, entries: list[dict]) -> None:
        status = agg["status"]
        self.result_card.setProperty("status", status)
        self.result_card.style().unpolish(self.result_card)
        self.result_card.style().polish(self.result_card)
        status_zh = {
            "INCOMPATIBLE": "INCOMPATIBLE 不兼容",
            "NEEDS_REVIEW": "NEEDS_REVIEW 待人工复核",
            "COMPATIBLE": "COMPATIBLE 兼容",
            "UNKNOWN": "UNKNOWN 无有效结果",
        }[status]
        self.card_title.setText(f"项目级结论:{status_zh}")
        counts = agg["counts"]
        self.card_detail.setText(
            f"风险等级 {agg['risk_level']}　·　成功 {agg['analyzed']}/{agg['total']} 文件\n"
            f"红 {counts['INCOMPATIBLE']}　黄 {counts['NEEDS_REVIEW']}　绿 {counts['COMPATIBLE']}"
            f"　·　命中片段文件 {agg['hit_files']}　歧义 {len(agg['ambiguous'])}"
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
                top.setText(0, f"✗ 解析失败：{path.name}　({e.get('error', '')[:120]})")
                top.setForeground(0, QBrush(QColor("#c62828")))
                self.table.addTopLevelItem(top)
                continue
            cr = rep.get("compliance_result") or {}
            st = cr.get("status") or "UNKNOWN"
            color = QColor(STATUS_COLOR.get(st, "#616161"))
            attr = rep.get("attribution") or {}
            amb = "⚠ 归属存在歧义，建议人工复核" if attr.get("attribution_ambiguous") else ""
            top.setText(0, f"● {path.name}")
            top.setForeground(0, QBrush(color))
            top.setText(8, amb)
            if amb:
                top.setForeground(8, QBrush(QColor("#e65100")))
            segs = rep.get("segments") or []
            top.setText(2, f"{st}｜{len(segs)} 片段")
            self.table.addTopLevelItem(top)
            for s in segs:
                lvl = s.get("verification_level")
                child = QTreeWidgetItem(
                    [
                        f"└ 片段#{s.get('id')}",
                        str(s.get("lines") or ""),
                        str(s.get("source") or ""),
                        str(s.get("license") or ""),
                        f"{s.get('similarity'):.3f}" if isinstance(s.get("similarity"), (int, float)) else "",
                        LEVEL_NAME.get(lvl, f"L{lvl}"),
                        "✓" if s.get("is_primary") else "",
                        "✓" if s.get("drives_conclusion") else "",
                    ]
                )
                child.setData(0, Qt.ItemDataRole.UserRole, {"path": str(path), "report": rep})
                top.addChild(child)
        self.table.expandAll()

    def render_methodology(self, agg: dict) -> None:
        ms = agg["methodologies"]
        if not ms:
            self.methodology_label.setText("方法学透明条：无可用 methodology 数据。")
            return
        ts_states = sorted({m.get("tree_sitter", "?") for m in ms})
        modes = sorted({str(m.get("retriever_mode", "?")) for m in ms})
        kb_counts = sorted({m.get("kb_files") for m in ms}, key=lambda x: (x is None, x))
        anchors = sorted({m.get("verification_min_anchor_lines") for m in ms}, key=lambda x: (x is None, x))
        degrade = "" if ts_states == ["available"] else "　⚠ 预处理存在正则降级！"
        self.methodology_label.setText(
            f"方法学透明条　tree_sitter: {'/'.join(ts_states)}{degrade}"
            f"　|　检索模式: {'/'.join(modes)}"
            f"　|　KB 文件数: {kb_counts}"
            f"　|　锚点行门槛: {anchors}"
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
        fname, _ = QFileDialog.getSaveFileName(
            self, "导出审计报告", default, f"*.{ext}"
        )
        if not fname:
            return
        agg = aggregate_project(self._results)
        parts: list[str] = []
        title = "LicTracer 项目许可证合规审计报告"
        if fmt == "markdown":
            head = [
                f"# {title}",
                "",
                "- 审计时间：见文件属性；形态：本地离线桌面端（代码不出本机）",
                f"- 审计文件：{agg['analyzed']}/{agg['total']} 成功；命中片段文件 {agg['hit_files']}",
                f"- **项目级结论：{agg['status']}（风险 {agg['risk_level']}）**",
                f"- 红 {agg['counts']['INCOMPATIBLE']} ／ 黄 {agg['counts']['NEEDS_REVIEW']} ／ 绿 {agg['counts']['COMPATIBLE']}",
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
            body_sections = []
            for e in self._results:
                inner = render(e["report"], "html") if e.get("report") else f"<p>✗ 解析失败：{e.get('error')}</p>"
                sec = inner.split("<body>", 1)[-1].split("</body>", 1)[0]
                body_sections.append(f"<section><h2 style='border-top:2px solid #ccc;padding-top:8px'>{e['path']}</h2>{sec}</section>")
            text = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{title}</title></head><body>"
                f"<h1>{title}</h1>"
                f"<p>项目级结论：<b style='color:{STATUS_COLOR.get(agg['status'], '#616161')}'>"
                f"{agg['status']}</b>（风险 {agg['risk_level']}）；"
                f"成功 {agg['analyzed']}/{agg['total']}；红 {agg['counts']['INCOMPATIBLE']} ／ "
                f"黄 {agg['counts']['NEEDS_REVIEW']} ／ 绿 {agg['counts']['COMPATIBLE']}</p>"
                + "".join(body_sections)
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

    def _persist_settings(self, license_: str, top_k: int, anchor: int) -> None:
        s = self._settings
        if self._folder:
            s.setValue("last_folder", str(self._folder))
        s.setValue("project_license", license_)
        s.setValue("top_k", top_k)
        s.setValue("min_anchor_lines", anchor)
        s.setValue("kb_override", self.kb_edit.text().strip())


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LicTracer")
    app.setOrganizationName("LicTracer")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
