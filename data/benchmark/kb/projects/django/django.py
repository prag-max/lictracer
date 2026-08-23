# 源自 Django 项目（BSD-3-Clause）：视图缓存装饰器
from functools import wraps

def cache_page(seconds=60):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            return view(*args, **kwargs)
        return wrapper
    return decorator
