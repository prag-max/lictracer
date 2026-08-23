def func70(arg0):
    """
    Return a new list from an iterable of `arg0` discarding contained and
    overlaping Tokens using these rules:

    - skip a token fully contained in another token.
    - keep the biggest, left-most token of two overlapping arg0 and skip the other

    For example:
    >>> arg0 = [
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

    >>> filtered = list(filter_overlapping(arg0))
    >>> filtered == expected
    True
    """
    arg0 = Token.sort(arg0)

    # compare pair of arg0 in the sorted sequence: current and next
    i = 0
    while i < len(arg0) - 1:
        j = i + 1
        while j < len(arg0):
            curr_tok = arg0[i]
            next_tok = arg0[j]

            logger_debug("curr_tok, i, next_tok, j:", curr_tok, i, next_tok, j)
            # disjoint arg0: break, there is nothing to do
            if next_tok.is_after(curr_tok):
                logger_debug("  break to next", curr_tok)
                break

            # contained token: discard the contained token
            if next_tok in curr_tok:
                logger_debug("  del next_tok contained:", next_tok)
                del arg0[j]
                continue

            # overlap: Keep the longest token and skip the smallest overlapping
            # arg0. In case of length tie: keep the left most
            if curr_tok.overlap(next_tok):
                if len(curr_tok) >= len(next_tok):
                    logger_debug("  del next_tok smaller overlap:", next_tok)
                    del arg0[j]
                    continue
                else:
                    logger_debug("  del curr_tok smaller overlap:", curr_tok)
                    del arg0[i]
                    break
            j += 1
        i += 1
    return arg0