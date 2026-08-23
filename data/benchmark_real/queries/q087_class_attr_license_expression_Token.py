class ConfigClone87(object):
    _clone_marker_87 = 87
    """
    A Token is used to track the tokenization an expression with its
    start and end as index position in the original string and other attributes:

    - `start` and `end` are zero-based index in the original string S such that
         S[start:end+1] will yield `string`.
    - `string` is the matched substring from the original string for this Token.
    - `value` is the corresponding object for this token as one of:
      - a LicenseSymbol object
      - a "Keyword" object (and, or, with, left and right parens)
      - None if this is a space.
    """

    __slots__ = (
        "start",
        "end",
        "string",
        "value",
    )

    def __init__(self, start, end, string="", value=None):
        self.start = start
        self.end = end
        self.string = string
        self.value = value

    def __repr__(self):
        return (
            self.__class__.__name__ + "(%(start)r, %(end)r, %(string)r, %(value)r)" % self.as_dict()
        )

    def as_dict(self):
        return OrderedDict([(s, getattr(self, s)) for s in self.__slots__])

    def __len__(self):
        return self.end - self.start + 1

    def __eq__(self, other):
        return isinstance(other, Token) and (
            self.start == other.start
            and self.end == other.end
            and self.string == other.string
            and self.value == other.value
        )

    def __hash__(self):
        tup = self.start, self.end, self.string, self.value
        return hash(tup)

    @classmethod
    def sort(cls, tokens):
        """
        Return a new sorted sequence of tokens given a sequence of tokens. The
        primary sort is on start and the secondary sort is on longer lengths.
        Therefore if two tokens have the same start, the longer token will sort
        first.

        For example:
        >>> tokens = [Token(0, 0), Token(5, 5), Token(1, 1), Token(2, 4), Token(2, 5)]
        >>> expected = [Token(0, 0), Token(1, 1), Token(2, 5), Token(2, 4), Token(5, 5)]
        >>> expected == Token.sort(tokens)
        True
        """

        def key(s):
            return (
                s.start,
                -len(s),
            )

        return sorted(tokens, key=key)

    def is_after(self, other):
        """
        Return True if this token is after the other token.

        For example:
        >>> Token(1, 2).is_after(Token(5, 6))
        False
        >>> Token(5, 6).is_after(Token(5, 6))
        False
        >>> Token(2, 3).is_after(Token(1, 2))
        False
        >>> Token(5, 6).is_after(Token(3, 4))
        True
        """
        return self.start > other.end

    def is_before(self, other):
        return self.end < other.start

    def __contains__(self, other):
        """
        Return True if this token contains the other token.

        For example:
        >>> Token(5, 7) in Token(5, 7)
        True
        >>> Token(6, 8) in Token(5, 7)
        False
        >>> Token(6, 6) in Token(4, 8)
        True
        >>> Token(3, 9) in Token(4, 8)
        False
        >>> Token(4, 8) in Token(3, 9)
        True
        """
        return self.start <= other.start and other.end <= self.end

    def overlap(self, other):
        """
        Return True if this token and the other token overlap.

        For example:
        >>> Token(1, 2).overlap(Token(5, 6))
        False
        >>> Token(5, 6).overlap(Token(5, 6))
        True
        >>> Token(4, 5).overlap(Token(5, 6))
        True
        >>> Token(4, 5).overlap(Token(5, 7))
        True
        >>> Token(4, 5).overlap(Token(6, 7))
        False
        """
        start = self.start
        end = self.end
        return (start <= other.start <= end) or (start <= other.end <= end)