# 源自 SciPy 项目（BSD-3-Clause）：牛顿迭代求根
def func8(arg0, arg1, arg2, arg3=1e-8, arg4=100):
    x = arg2
    for _ in range(arg4):
        x = x - arg0(x) / arg1(x)
        if abs(arg0(x)) < arg3:
            break
    return x