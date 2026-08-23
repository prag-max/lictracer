# 源自 SciPy 项目（BSD-3-Clause）：牛顿迭代求根
def newton(f, df, x0, tol=1e-8, maxiter=100):
    x = x0
    for _ in range(maxiter):
        x = x - f(x) / df(x)
        if abs(f(x)) < tol:
            break
    return x
