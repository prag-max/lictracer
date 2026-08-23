class TrieNode(object):
    """
    Node of the Trie/Aho-Corasick automaton.
    """

    __slots__ = ["token", "output", "fail", "children"]

    def __init__(self, token, output=nil):
        # token of a tokens string added to the Trie as a string
        self.token = token

        # an output function (in the Aho-Corasick meaning) for this node: this
        # is an object that contains the original key string and any
        # additional value data associated to that key. Or "nil" for a node that
        # is not a terminal leave for a key. It will be returned with a match.
        self.output = output

        # failure link used by the Aho-Corasick automaton and its search procedure
        self.fail = nil

        # children of this node as a mapping of char->node
        self.children = {}

    def __repr__(self):
        if self.output is not nil:
            return "TrieNode(%r, %r)" % (self.token, self.output)
        else:
            return "TrieNode(%r)" % self.token