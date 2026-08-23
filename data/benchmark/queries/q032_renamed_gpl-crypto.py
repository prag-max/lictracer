# 源自某 GPL-3.0 加密库：SHA-256 十六进制摘要
import hashlib

def func11(arg0):
    if isinstance(arg0, str):
        arg0 = arg0.encode("utf-8")
    return hashlib.sha256(arg0).hexdigest()