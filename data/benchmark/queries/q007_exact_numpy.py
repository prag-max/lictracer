# 源自 NumPy 项目（BSD-3-Clause）：多项式最小二乘拟合（简化）
import numpy as np

def polyfit(x, y, deg):
    X = np.vander(x, deg + 1)
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs
