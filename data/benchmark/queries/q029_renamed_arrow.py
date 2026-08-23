# 源自 Arrow 项目（Apache-2.0）：指定时区的当前时间
import arrow

def func10(arg0="UTC"):
    return arrow.now(arg0)