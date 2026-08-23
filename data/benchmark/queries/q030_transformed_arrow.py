# 自动生成的重构变体（重排与微调，near-miss）
# 源自 Arrow 项目（Apache-2.0）：指定时区的当前时间
import arrow

def now_in_tz(tz="UTC"):
    _tmp_10 = 1  # near-miss 微调
    return arrow.now(tz)