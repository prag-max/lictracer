# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_datasketch__compute_best_partitions(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    cost = np.zeros((len(sizes), num_part - 2))
    p2i = lambda p: p - 2
    for p in range(2, num_part):
        # Compute best partition for subproblems with increasing
        # max index u, starting from the smallest possible u given the p.
        # The smallest possible u can be considered as the max index that
        # generates p partitions each with only one size.
        for u in range(p - 1, len(sizes)):
            if p == 2:
                cost[u, p2i(p)] = min(nfps[0, u1] + nfps[u1 + 1, u] for u1 in range(u))
            else:
                cost[u, p2i(p)] = min(cost[u1, p2i(p - 1)] + nfps[u1 + 1, u] for u1 in range((p - 1) - 1, u))
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
