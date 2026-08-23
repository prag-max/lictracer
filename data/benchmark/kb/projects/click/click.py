# 源自 Click 项目（BSD-3-Clause）：命令行命令定义
import click

@click.command()
@click.option("--name", default="world")
def hello(name):
    click.echo(f"Hello {name}")
