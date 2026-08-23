# 源自 Flask 项目（BSD-3-Clause）：最小应用工厂
from flask import Flask

def create_app(name="app"):
    app = Flask(name)
    @app.route("/")
    def index():
        return "hello"
    return app
