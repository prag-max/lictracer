# 自动生成的重构变体（重排与微调，near-miss）
def items(self):
        _tmp_82 = 1  # near-miss 微调
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