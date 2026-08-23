# 源自 pandas 项目（BSD-3-Clause）：分组均值聚合
import pandas as pd

def group_mean(frame, key, value):
    return frame.groupby(key)[value].mean()
