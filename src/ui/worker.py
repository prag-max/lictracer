# -*- coding: utf-8 -*-
"""后台分析线程：批量调用 analyze_file，信号驱动进度与结果，支持取消。

设计要点：
- analyze_file 为同步阻塞调用，必须运行在工作线程（QThread.run），
  主线程仅通过信号接收进度/结果，保证界面不冻结；
- 单文件异常被捕获为该文件的 error 字段，**不中断整批**；
- 取消为协作式：在「下一个文件开始前」生效（当前文件执行中不可打断）。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.pipeline import analyze_file


class AnalyzeWorker(QThread):
    progress = Signal(int, int, str)  # 已完成数, 总数, 当前文件名
    file_done = Signal(str, object, str)  # path, report(dict)|None, error(空串=成功)
    batch_done = Signal(list)  # 全部 entry：[{"path","report","error"}]

    def __init__(
        self,
        files,
        *,
        project_license,
        top_k,
        kb_path=None,
        min_anchor_lines=None,
        parent=None,
    ):
        super().__init__(parent)
        self._files = [Path(f) for f in files]
        self._project_license = project_license
        self._top_k = top_k
        self._kb_path = str(kb_path) if kb_path else None
        self._min_anchor_lines = min_anchor_lines
        self._cancelled = False

    def cancel(self) -> None:
        """请求取消；在当前文件完成后停止后续文件。"""
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        entries: list[dict] = []
        total = len(self._files)
        for i, f in enumerate(self._files):
            if self._cancelled:
                break
            self.progress.emit(i, total, f.name)
            try:
                report = analyze_file(
                    f,
                    project_license=self._project_license,
                    top_k=self._top_k,
                    kb_path=self._kb_path,
                    min_anchor_lines=self._min_anchor_lines,
                )
                entries.append({"path": f, "report": report, "error": ""})
                self.file_done.emit(str(f), report, "")
            except Exception as exc:  # noqa: BLE001 —— 单文件失败不拖垮整批
                msg = f"{type(exc).__name__}: {exc}"
                entries.append({"path": f, "report": None, "error": msg})
                self.file_done.emit(str(f), None, msg)
        self.progress.emit(len(entries), total, "")
        self.batch_done.emit(entries)
