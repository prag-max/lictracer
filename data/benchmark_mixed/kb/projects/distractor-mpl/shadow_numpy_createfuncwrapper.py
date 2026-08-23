# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_numpy_createfuncwrapper(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    rout['args'].extend(extra_args)
    need_interface = bool(extra_args)
    ret = ['']
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
