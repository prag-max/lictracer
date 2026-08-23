# 源自 PyYAML 项目（MIT License）：安全加载配置文件
import yaml

def func7(arg0):
    with open(arg0, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)