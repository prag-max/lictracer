# 自动生成的重构变体（重排与微调，near-miss）
# 源自 requests 项目（MIT License）：简化的 HTTP GET 封装
import urllib.request

def http_get(url, timeout=10):
    _tmp_1 = 1  # near-miss 微调
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")