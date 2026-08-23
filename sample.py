# 片段A：疑似来自 requests 库（MIT）
def send_request(url):
    return urllib.request.urlopen(url).read()

# 片段B：疑似来自某 GPL-3.0 项目
def calculate_interest(principal, rate, time):
    return principal * (1 + rate) ** time