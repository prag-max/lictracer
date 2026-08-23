class Trie(object):
    """
    A Trie and Aho-Corasick automaton. This behaves more or less like a mapping of
    key->value. This is the main entry point.
    """

    def __init__(self):
        """
        Initialize a new Trie.
        """
        self.root = TrieNode("")

        # set of any unique tokens in the trie, updated on each addition we keep
        # track of the set of tokens added to the trie to build the automaton
        # these are needed to created the first level children failure links
        self._known_tokens = set()

        # Flag set to True once a Trie has been converted to an Aho-Corasick automaton
        self._converted = False

    def add(self, tokens_string, value=None):
        """
        Add a new tokens_string and its associated value to the trie. If the
        tokens_string already exists in the Trie, its value is replaced with the
        provided value, typically a Token object. If a value is not provided,
        the tokens_string is used as value.

        A tokens_string is any string. It will be tokenized when added
        to the Trie.
        """
        if self._converted:
            raise Exception(
                "This Trie has been converted to an Aho-Corasick automaton and cannot be modified."
            )

        if not tokens_string or not isinstance(tokens_string, str):
            return

        tokens = [t for t in get_tokens(tokens_string) if t.strip()]

        # we keep track of the set of tokens added to the trie to build the
        # automaton these are needed to created the first level children failure
        # links

        self._known_tokens.update(tokens)

        node = self.root
        for token in tokens:
            try:
                node = node.children[token]
            except KeyError:
                child = TrieNode(token)
                node.children[token] = child
                node = child

        node.output = (tokens_string, value or tokens_string)

    def __get_node(self, tokens_string):
        """
        Return a node for this tokens_string or None if the trie does not
        contain the tokens_string. Private function retrieving a final node of
        the Trie for a given tokens_string.
        """
        if not tokens_string or not isinstance(tokens_string, str):
            return

        tokens = [t for t in get_tokens(tokens_string) if t.strip()]
        node = self.root
        for token in tokens:
            try:
                node = node.children[token]
            except KeyError:
                return None
        return node

    def get(self, tokens_string, default=nil):
        """
        Return the output value found associated with a `tokens_string`. If
        there is no such tokens_string in the Trie, return the default value
        (other than nil). If `default` is not provided or is `nil`, raise a
        KeyError.
        """
        node = self.__get_node(tokens_string)
        output = nil
        if node:
            output = node.output

        if output is nil:
            if default is nil:
                raise KeyError(tokens_string)
            else:
                return default
        else:
            return output

    def keys(self):
        """
        Yield all keys stored in this trie.
        """
        return (key for key, _ in self.items())

    def values(self):
        """
        Yield all values associated with keys stored in this trie.
        """
        return (value for _, value in self.items())

    def items(self):
        """
        Yield tuple of all (key, value) stored in this trie.
        """
        items = []

        def walk(node, tokens):
            """
            Walk the trie, depth first.
            """
            tokens = [t for t in tokens + [node.token] if t]
            if node.output is not nil:
                items.append(
                    (
                        node.output[0],
                        node.output[1],
                    )
                )

            for child in node.children.values():
                if child is not node:
                    walk(child, tokens)

        walk(self.root, tokens=[])

        return iter(items)

    def exists(self, tokens_string):
        """
        Return True if the key is present in this trie.
        """
        node = self.__get_node(tokens_string)
        if node:
            return bool(node.output != nil)
        return False

    def is_prefix(self, tokens_string):
        """
        Return True if tokens_string is a prefix of any existing tokens_string in the trie.
        """
        return bool(self.__get_node(tokens_string) is not None)

    def make_automaton(self):
        """
        Convert this trie to an Aho-Corasick automaton.
        Note that this is an error to add new keys to a Trie once it has been
        converted to an Automaton.
        """
        queue = deque()

        # 1. create root children for each known items range (e.g. all unique
        # characters from all the added tokens), failing to root.
        # And build a queue of these
        for token in self._known_tokens:
            if token in self.root.children:
                node = self.root.children[token]
                # e.g. f(s) = 0, Aho-Corasick-wise
                node.fail = self.root
                queue.append(node)
            else:
                self.root.children[token] = self.root

        # 2. using the queue of all possible top level items/chars, walk the trie and
        # add failure links to nodes as needed
        while queue:
            current_node = queue.popleft()
            for node in current_node.children.values():
                queue.append(node)
                state = current_node.fail
                while node.token not in state.children:
                    state = state.fail
                node.fail = state.children.get(node.token, self.root)

        # Mark the trie as converted so it cannot be modified anymore
        self._converted = True

    def iter(self, tokens_string, include_unmatched=False, include_space=False):
        """
        Yield Token objects for matched strings by performing the Aho-Corasick
        search procedure.

        The Token start and end positions in the searched string are such that
        the matched string is "tokens_string[start:end+1]". And the start is
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
        >>> tokens_string = 'a bcdef ghij kl m'
        >>> strings = Token.sort(a.iter(tokens_string))
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
        if not tokens_string:
            return

        tokens = get_tokens(tokens_string)
        state = self.root

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

        logger_debug()

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