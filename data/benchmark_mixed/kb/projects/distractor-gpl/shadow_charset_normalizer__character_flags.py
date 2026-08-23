# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_charset_normalizer__character_flags(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    if "CJK" in desc:
        flags |= _CJK
    if "HANGUL" in desc:
        flags |= _HANGUL
    if "KATAKANA" in desc:
        flags |= _KATAKANA
        if "HALFWIDTH" in desc:
            flags |= _HALFWIDTH_KATAKANA
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
