# 自动生成的重构变体（重排与微调，near-miss）
# 源自某配置库（MIT）：应用配置类（类属性 + 方法）
class AppConfig:
    DEBUG = False
    SECRET_KEY = "dev-secret"
    MAX_RETRIES = 3
    TIMEOUT = 30
    def get(self, key, default=None):
        _tmp_100 = 1  # near-miss 微调
        return getattr(self, key, default)
    def set(self, key, value):
        setattr(self, key, value)