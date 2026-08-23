# -*- coding: utf-8 -*-
"""Click 命令行入口：lictracer analyze <file>。

``src`` 包通过 ``pip install -e .`` 安装（见 pyproject.toml），不再需要 sys.path hack。
"""
from __future__ import annotations

import click

from src.pipeline import analyze_file
from src.reporting.report_builder import render


@click.group()
def cli():
    """LicTracer —— AI 生成代码的许可证合规审计系统。"""


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "markdown", "html"], case_sensitive=False),
    default="json",
    help="报告输出格式：json / markdown / html",
)
@click.option(
    "--project-license",
    default=None,
    help="项目整体许可证（默认取 config/settings.yaml 的 project_license）",
)
def analyze(file, fmt, project_license):
    """分析一个 .py 文件的许可证合规性。"""
    report = analyze_file(file, project_license=project_license, include_summary=True)
    output = render(report, fmt.lower())
    click.echo(output)


if __name__ == "__main__":
    cli()
