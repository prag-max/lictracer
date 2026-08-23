# 源自某配置库（MIT）：应用配置类（类属性 + 方法）
class AppConfig:
    DEBUG = False
    SECRET_KEY = "dev-secret"
    MAX_RETRIES = 3
    TIMEOUT = 30
    def func100(arg0, arg1, arg2=None):
        return getattr(arg0, arg1, arg2)
    def func100(arg0, arg1, arg2):
        setattr(arg0, arg1, arg2)