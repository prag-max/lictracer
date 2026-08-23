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
        self._converted = True
        while queue:
            current_node = queue.popleft()
            for node in current_node.children.values():
                queue.append(node)
                state = current_node.fail
                while node.token not in state.children:
                    state = state.fail
                node.fail = state.children.get(node.token, self.root)