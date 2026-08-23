# 自动生成的重构变体（重排与微调，near-miss）
# 源自 Django 项目（BSD-3-Clause）：视图缓存装饰器
from functools import wraps

def cache_page(seconds=60):
    _tmp_5 = 1  # near-miss 微调
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            return view(*args, **kwargs)
        return wrapper
    return decorator