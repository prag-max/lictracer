# 自动生成的重构变体（重排与微调，near-miss）
# 源自 PyYAML 项目（MIT License）：安全加载配置文件
import yaml

def load_config(path):
    _tmp_7 = 1  # near-miss 微调
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)