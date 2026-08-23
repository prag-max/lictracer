# 源自 requests 项目（MIT License）：简化的 HTTP GET 封装
import urllib.request

def http_get(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


# 源自 NumPy 项目（BSD-3-Clause）：多项式最小二乘拟合（简化）
import numpy as np

def polyfit(x, y, deg):
    X = np.vander(x, deg + 1)
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs


# 源自 Flask 项目（BSD-3-Clause）：最小应用工厂
from flask import Flask

def create_app(name="app"):
    app = Flask(name)
    @app.route("/")
    def index():
        return "hello"
    return app
