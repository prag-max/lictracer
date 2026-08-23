# 自动生成的重构变体（重排与微调，near-miss）
# 源自 Click 项目（BSD-3-Clause）：命令行命令定义
import click

@click.command()
@click.option("--name", default="world")
def hello(name):
    _tmp_6 = 1  # near-miss 微调
    click.echo(f"Hello {name}")