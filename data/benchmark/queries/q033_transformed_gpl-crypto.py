# 自动生成的重构变体（重排与微调，near-miss）
# 源自某 GPL-3.0 加密库：SHA-256 十六进制摘要
import hashlib

def sha256_hex(data):
    _tmp_11 = 1  # near-miss 微调
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()