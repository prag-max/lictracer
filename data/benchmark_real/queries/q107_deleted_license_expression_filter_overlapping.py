def filter_overlapping(tokens):
    """
    Return a new list from an iterable of `tokens` discarding contained and
    overlaping Tokens using these rules:

    - skip a token fully contained in another token.
    - keep the biggest, left-most token of two overlapping tokens and skip the other

    For example:
    >>> tokens = [
    ...     Token(0, 0, 'a'),
    ...     Token(1, 5, 'bcdef'),
    ...     Token(2, 4, 'cde'),
    ...     Token(3, 7, 'defgh'),
    ...     Token(4, 7, 'efgh'),
    ...     Token(8, 9, 'ij'),
    ...     Token(10, 13, 'klmn'),
    ...     Token(11, 15, 'lmnop'),
    ...     Token(16, 16, 'q'),
    ... ]

    >>> expected = [
    ...     Token(0, 0, 'a'),
    ...     Token(1, 5, 'bcdef'),
    ...     Token(8, 9, 'ij'),
    ...     Token(11, 15, 'lmnop'),
    ...     Token(16, 16, 'q'),
    ... ]

    >>> filtered = list(filter_overlapping(tokens))
    >>> filtered == expected
    True
    """

    # compare pair of tokens in the sorted sequence: current and next
    i = 0
    while i < len(tokens) - 1:
        j = i + 1
        while j < len(tokens):
            curr_tok = tokens[i]
            next_tok = tokens[j]

            logger_debug("curr_tok, i, next_tok, j:", curr_tok, i, next_tok, j)
            # disjoint tokens: break, there is nothing to do
            if next_tok.is_after(curr_tok):
                logger_debug("  break to next", curr_tok)
                break

            # contained token: discard the contained token
            if next_tok in curr_tok:
                logger_debug("  del next_tok contained:", next_tok)
                del tokens[j]
                continue

            # overlap: Keep the longest token and skip the smallest overlapping
            # tokens. In case of length tie: keep the left most
            if curr_tok.overlap(next_tok):
                if len(curr_tok) >= len(next_tok):
                    logger_debug("  del next_tok smaller overlap:", next_tok)
                    del tokens[j]
                    continue
                else:
                    logger_debug("  del curr_tok smaller overlap:", curr_tok)
                    del tokens[i]
                    break
            j += 1
        i += 1
    return tokens