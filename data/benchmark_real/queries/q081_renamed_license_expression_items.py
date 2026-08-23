def func80(arg0):
        """
        Yield tuple of all (key, value) stored in this trie.
        """
        items = []

        def func80(arg0, arg1):
            """
            Walk the trie, depth first.
            """
            arg1 = [t for t in arg1 + [arg0.token] if t]
            if arg0.output is not nil:
                items.append(
                    (
                        arg0.output[0],
                        arg0.output[1],
                    )
                )

            for child in arg0.children.values():
                if child is not arg0:
                    walk(child, arg1)

        walk(self.root, arg1=[])

        return iter(items)