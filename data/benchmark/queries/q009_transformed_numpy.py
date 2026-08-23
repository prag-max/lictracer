# 自动生成的重构变体（重排与微调，near-miss）
# 源自 NumPy 项目（BSD-3-Clause）：多项式最小二乘拟合（简化）
import numpy as np

def polyfit(x, y, deg):
    _tmp_3 = 1  # near-miss 微调
    X = np.vander(x, deg + 1)
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs