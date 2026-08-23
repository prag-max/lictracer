def tokenize(self, string, include_unmatched=True, include_space=False):
        """
        Tokenize a string for matched and unmatched sub-sequences and yield non-
        overlapping Token objects performing a modified Aho-Corasick search
        procedure:

        - return both matched and unmatched sub-sequences.
        - do not return matches with positions that are contained or overlap with
          another match:
          - discard smaller matches contained in a larger match.
          - when there is overlap (but not containment), the matches are sorted by
            start and biggest length and then:
             - we return the largest match of two overlaping matches
             - if they have the same length, keep the match starting the earliest and
               return the non-overlapping portion of the other discarded match as a
               non-match.

        Each Token contains the start and end position, the corresponding string
        and an associated value object.

        For example:
        >>> a = Trie()
        >>> a.add('BCDEF')
        >>> a.add('CDE')
        >>> a.add('DEFGH')
        >>> a.add('EFGH')
        >>> a.add('KL')
        >>> a.make_automaton()
        >>> string = 'a bcdef ghij kl'
        >>> tokens = list(a.tokenize(string, include_space=True))

        >>> expected = [
        ...     Token(0, 0, u'a', None),
        ...     Token(1, 1, u' ', None),
        ...     Token(2, 6, u'bcdef', u'BCDEF'),
        ...     Token(7, 7, u' ', None),
        ...     Token(8, 11, u'ghij', None),
        ...     Token(12, 12, u' ', None),
        ...     Token(13, 14, u'kl', u'KL')
        ... ]
        >>> tokens == expected
        True
        """
        tokens = self.iter(string, include_unmatched=include_unmatched, include_space=include_space)
        tokens = list(tokens)
        if TRACE:
            logger_debug("tokenize.tokens:", tokens)
        if not include_space:
            tokens = [t for t in tokens if t.string.strip()]
        tokens = filter_overlapping(tokens)
        return tokens