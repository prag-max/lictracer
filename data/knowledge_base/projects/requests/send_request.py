# 来自 requests 库：发送 HTTP 请求（MIT）
def send_request(url):
    return urllib.request.urlopen(url).read()