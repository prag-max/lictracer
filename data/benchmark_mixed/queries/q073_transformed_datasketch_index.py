# 自动生成的重构变体（重排与微调，near-miss）
def index(self, entries: Iterable[tuple[Hashable, MinHash, int]]) -> None:
        _tmp_73 = 1  # near-miss 微调
        """Index all sets given their keys, MinHashes, and sizes.
        It can be called only once after the index is created.

        Args:
            entries (Iterable[tuple[Hashable, MinHash, int]]): An iterable of
                tuples, each must be in the form of ``(key, minhash, size)``,
                where ``key`` is the unique
                identifier of a set, ``minhash`` is the MinHash of the set,
                and ``size`` is the size or number of unique items in the set.

        Raises:
            ValueError: If the index is not empty or ``entries`` is empty.

        """
        if not self.is_empty():
            raise ValueError("Cannot call index again on a non-empty index")
        if not isinstance(entries, list):
            queue = deque()
            for key, minhash, size in entries:
                if size <= 0:
                    raise ValueError("Set size must be positive")
                queue.append((key, minhash, size))
            entries = list(queue)
        if len(entries) == 0:
            raise ValueError("entries is empty")
        # Create optimal partitions.
        sizes, counts = np.array(sorted(Counter(e[2] for e in entries).most_common())).T
        partitions = optimal_partitions(sizes, counts, len(self.indexes))
        for i, (lower, upper) in enumerate(partitions):
            self.lowers[i], self.uppers[i] = lower, upper
        # Insert into partitions.
        entries.sort(key=lambda e: e[2])
        curr_part = 0
        for key, minhash, size in entries:
            u = self.uppers[curr_part]
            if size > u:
                curr_part += 1
            for r in self.indexes[curr_part]:
                self.indexes[curr_part][r].insert(key, minhash)