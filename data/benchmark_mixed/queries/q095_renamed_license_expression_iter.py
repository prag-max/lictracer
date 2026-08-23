def func94(arg0, arg1, arg2=False, arg3=False):
        """
        Yield Token objects for matched strings by performing the Aho-Corasick
        search procedure.

        The Token start and end positions in the searched string are such that
        the matched string is "arg1[start:end+1]". And the start is
        computed from the end_index collected by the Aho-Corasick search
        procedure such that
        "start=end_index - n + 1" where n is the length of a matched string.

        The Token.value is an object associated with a matched string.

        For example:
        >>> a = Trie()
        >>> a.add('BCDEF')
        >>> a.add('CDE')
        >>> a.add('DEFGH')
        >>> a.add('EFGH')
        >>> a.add('KL')
        >>> a.make_automaton()
        >>> arg1 = 'a bcdef ghij kl m'
        >>> strings = Token.sort(a.iter(arg1))
        >>> expected = [
        ...     Token(2, 6, u'bcdef', u'BCDEF'),
        ...     Token(13, 14, u'kl', u'KL')
        ... ]

        >>> strings == expected
        True

        >>> list(a.iter('')) == []
        True

        >>> list(a.iter(' ')) == []
        True
        """
        if not arg1:
            return

        tokens = get_tokens(arg1)
        state = arg0.root

        if TRACE:
            logger_debug("Trie.iter() with:", repr(arg1))
            logger_debug(" tokens:", tokens)

        end_pos = -1
        for token_string in tokens:
            end_pos += len(token_string)
            if TRACE:
                logger_debug()
                logger_debug("token_string", repr(token_string))
                logger_debug(" end_pos", end_pos)

            if not arg3 and not token_string.strip():
                if TRACE:
                    logger_debug("  arg3 skipped")
                continue

            if token_string not in arg0._known_tokens:
                state = arg0.root
                if TRACE:
                    logger_debug("  unmatched")
                if arg2:
                    n = len(token_string)
                    start_pos = end_pos - n + 1
                    tok = Token(
                        start=start_pos,
                        end=end_pos,
                        string=arg1[start_pos : end_pos + 1],
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
            state = state.children.get(token_string, arg0.root)
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
                        start_pos, end_pos, arg1[start_pos : end_pos + 1], output_value
                    )
                    yielded = True
                match = match.fail
            if not yielded and arg2:
                if TRACE:
                    logger_debug("  unmatched but known token")
                n = len(token_string)
                start_pos = end_pos - n + 1
                tok = Token(start_pos, end_pos, arg1[start_pos : end_pos + 1], None)
                if TRACE:
                    logger_debug("  unmatched tok 2:", tok)
                yield tok

        logger_debug()