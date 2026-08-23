# 源自某配置库（MIT）：应用配置类（类属性 + 方法）
class AppConfig:
    DEBUG = False
    SECRET_KEY = "dev-secret"
    MAX_RETRIES = 3
    TIMEOUT = 30
    def get(self, key, default=None):
        return getattr(self, key, default)
    def set(self, key, value):
        setattr(self, key, value)
