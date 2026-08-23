# 源自 Celery 项目（BSD-3-Clause）：任务定义
from celery import Celery

app = Celery("tasks", broker="redis://localhost")

@app.task
def add(a, b):
    return a + b
