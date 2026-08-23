# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_pandas_git_pieces_from_vcs(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    env.pop("GIT_DIR", None)
    runner = functools.partial(runner, env=env)
    _, rc = runner(GITS, ["rev-parse", "--git-dir"], cwd=root, hide_stderr=not verbose)
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
