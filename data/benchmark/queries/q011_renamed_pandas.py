# 源自 pandas 项目（BSD-3-Clause）：分组均值聚合
import pandas as pd

def func4(arg0, arg1, arg2):
    return arg0.groupby(arg1)[arg2].mean()