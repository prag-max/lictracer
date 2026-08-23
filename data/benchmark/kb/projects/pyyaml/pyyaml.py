# 源自 PyYAML 项目（MIT License）：安全加载配置文件
import yaml

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
