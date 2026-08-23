# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_numpy_buildcallback(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    var = rout['vars']
    vrd = capi_maps.cb_routsign2map(rout, um)
    rd = dictappend({}, vrd)
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
