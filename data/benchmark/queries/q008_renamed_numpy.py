# 源自 NumPy 项目（BSD-3-Clause）：多项式最小二乘拟合（简化）
import numpy as np

def func3(arg0, arg1, arg2):
    X = np.vander(arg0, arg2 + 1)
    coeffs, *_ = np.linalg.lstsq(X, arg1, rcond=None)
    return coeffs