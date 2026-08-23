# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_pandas_bootstrap_plot(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    medians = np.array([np.median(sampling) for sampling in samplings])
    midranges = np.array(
        [(min(sampling) + max(sampling)) * 0.5 for sampling in samplings]
    )
    if fig is None:
        fig = plt.figure()
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
