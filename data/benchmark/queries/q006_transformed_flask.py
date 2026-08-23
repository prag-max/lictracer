# 自动生成的重构变体（重排与微调，near-miss）
# 源自 Flask 项目（BSD-3-Clause）：最小应用工厂
from flask import Flask

def create_app(name="app"):
    _tmp_2 = 1  # near-miss 微调
    app = Flask(name)
    @app.route("/")
    def index():
        return "hello"
    return app