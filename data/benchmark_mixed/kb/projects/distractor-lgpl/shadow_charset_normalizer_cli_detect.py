# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_charset_normalizer_cli_detect(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
    parser.add_argument(
        "-a",
        "--with-alternative",
        action="store_true",
        default=False,
        dest="alternatives",
        help="Output complementary possibilities if any. Top-level JSON WILL be a list.",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        default=False,
        dest="normalize",
        help="Permit to normalize input file. If not set, program does not write anything.",
    )
    parser.add_argument(
        "-m",
        "--minimal",
        action="store_true",
        default=False,
        dest="minimal",
        help="Only output the charset detected to STDOUT. Disabling JSON output.",
    )
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
