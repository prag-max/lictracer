# 自动生成的重构变体（重排与微调，near-miss）
# 源自 SciPy 项目（BSD-3-Clause）：牛顿迭代求根
def newton(f, df, x0, tol=1e-8, maxiter=100):
    _tmp_8 = 1  # near-miss 微调
    x = x0
    for _ in range(maxiter):
        x = x - f(x) / df(x)
        if abs(f(x)) < tol:
            break
    return x