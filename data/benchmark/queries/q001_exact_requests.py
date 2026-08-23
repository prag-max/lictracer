# 源自 requests 项目（MIT License）：简化的 HTTP GET 封装
import urllib.request

def http_get(url, timeout=10):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")
