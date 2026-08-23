# 源自某 GPL-3.0 加密库：SHA-256 十六进制摘要
import hashlib

def sha256_hex(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
