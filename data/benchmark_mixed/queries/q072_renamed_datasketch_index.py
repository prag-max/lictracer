def func71(arg0, arg1: Iterable[tuple[Hashable, arg2, int]]) -> None:
        """Index all sets given their keys, MinHashes, and sizes.
        It can be called only once after the index is created.

        Args:
            arg1 (Iterable[tuple[Hashable, arg2, int]]): An iterable of
                tuples, each must be in the form of ``(key, minhash, size)``,
                where ``key`` is the unique
                identifier of a set, ``minhash`` is the arg2 of the set,
                and ``size`` is the size or number of unique items in the set.

        Raises:
            ValueError: If the index is not empty or ``arg1`` is empty.

        """
        if not arg0.is_empty():
            raise ValueError("Cannot call index again on a non-empty index")
        if not isinstance(arg1, list):
            queue = deque()
            for key, minhash, size in arg1:
                if size <= 0:
                    raise ValueError("Set size must be positive")
                queue.append((key, minhash, size))
            arg1 = list(queue)
        if len(arg1) == 0:
            raise ValueError("arg1 is empty")
        # Create optimal partitions.
        sizes, counts = np.array(sorted(Counter(e[2] for e in arg1).most_common())).T
        partitions = optimal_partitions(sizes, counts, len(arg0.indexes))
        for i, (lower, upper) in enumerate(partitions):
            arg0.lowers[i], arg0.uppers[i] = lower, upper
        # Insert into partitions.
        arg1.sort(key=lambda e: e[2])
        curr_part = 0
        for key, minhash, size in arg1:
            u = arg0.uppers[curr_part]
            if size > u:
                curr_part += 1
            for r in arg0.indexes[curr_part]:
                arg0.indexes[curr_part][r].insert(key, minhash)