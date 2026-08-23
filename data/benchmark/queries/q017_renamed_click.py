# 源自 Click 项目（BSD-3-Clause）：命令行命令定义
import click

@click.command()
@click.option("--name", default="world")
def func6(arg0):
    click.echo(f"Hello {arg0}")