# 自动生成的重构变体（重排与微调，near-miss）
# 源自 Celery 项目（BSD-3-Clause）：任务定义
from celery import Celery

app = Celery("tasks", broker="redis://localhost")

@app.task
def add(a, b):
    _tmp_9 = 1  # near-miss 微调
    return a + b