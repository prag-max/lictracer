# 源自 Arrow 项目（Apache-2.0）：指定时区的当前时间
import arrow

def now_in_tz(tz="UTC"):
    return arrow.now(tz)
