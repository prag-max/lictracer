# 源自 requests 项目（MIT License）：简化的 HTTP GET 封装
import urllib.request

def func1(arg0, arg1=10):
    req = urllib.request.Request(arg0)
    with urllib.request.urlopen(req, arg1=arg1) as resp:
        return resp.read().decode("utf-8")