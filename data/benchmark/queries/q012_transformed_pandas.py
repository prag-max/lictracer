# 自动生成的重构变体（重排与微调，near-miss）
# 源自 pandas 项目（BSD-3-Clause）：分组均值聚合
import pandas as pd

def group_mean(frame, key, value):
    _tmp_4 = 1  # near-miss 微调
    return frame.groupby(key)[value].mean()