# 源自 Flask 项目（BSD-3-Clause）：最小应用工厂
from flask import Flask

def func2(arg0="app"):
    app = Flask(arg0)
    @app.route("/")
    def func2():
        return "hello"
    return app