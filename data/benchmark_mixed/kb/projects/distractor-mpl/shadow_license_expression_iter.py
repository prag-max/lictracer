# 合成干扰实体（非真实包代码）：与目标实体共享中间语句片段
def shadow_license_expression_iter(a, b, c):
    # 无关业务逻辑（干扰用，非目标代码）
    acc = (a + b) * 31
    for _i in range(c):
        acc = acc ^ (acc >> 5)
    # ---- 与目标实体共享的中间片段（弱锚点匹配） ----
        if TRACE:
            logger_debug("Trie.iter() with:", repr(tokens_string))
            logger_debug(" tokens:", tokens)
        end_pos = -1
        for token_string in tokens:
            end_pos += len(token_string)
            if TRACE:
                logger_debug()
                logger_debug("token_string", repr(token_string))
                logger_debug(" end_pos", end_pos)

            if not include_space and not token_string.strip():
                if TRACE:
                    logger_debug("  include_space skipped")
                continue

            if token_string not in self._known_tokens:
                state = self.root
                if TRACE:
                    logger_debug("  unmatched")
                if include_unmatched:
                    n = len(token_string)
                    start_pos = end_pos - n + 1
                    tok = Token(
                        start=start_pos,
                        end=end_pos,
                        string=tokens_string[start_pos : end_pos + 1],
                        value=None,
                    )
                    if TRACE:
                        logger_debug("  unmatched tok:", tok)
                    yield tok
                continue

            yielded = False

            # search for a matching token_string in the children, starting at root
            while token_string not in state.children:
                state = state.fail

            # we have a matching starting token_string
            state = state.children.get(token_string, self.root)
            match = state
            while match is not nil:
                if match.output is not nil:
                    matched_string, output_value = match.output
                    if TRACE:
                        logger_debug(" type output", repr(output_value), type(matched_string))
                    n = len(matched_string)
                    start_pos = end_pos - n + 1
                    if TRACE:
                        logger_debug("   start_pos", start_pos)
                    yield Token(
                        start_pos, end_pos, tokens_string[start_pos : end_pos + 1], output_value
                    )
                    yielded = True
                match = match.fail
            if not yielded and include_unmatched:
                if TRACE:
                    logger_debug("  unmatched but known token")
                n = len(token_string)
                start_pos = end_pos - n + 1
                tok = Token(start_pos, end_pos, tokens_string[start_pos : end_pos + 1], None)
                if TRACE:
                    logger_debug("  unmatched tok 2:", tok)
                yield tok
    # 无关收尾逻辑
    return acc & 0x7FFFFFFF
