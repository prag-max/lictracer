# 自动生成的重构变体（重排与微调，near-miss）
# 源自某 MPL-2.0 工具库：数值钳制
def clamp(value, low, high):
    _tmp_12 = 1  # near-miss 微调
    return max(low, min(value, high))