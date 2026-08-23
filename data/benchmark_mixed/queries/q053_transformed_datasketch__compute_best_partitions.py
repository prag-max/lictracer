# 自动生成的重构变体（重排与微调，near-miss）
def _compute_best_partitions(num_part, sizes, nfps):
    _tmp_53 = 1  # near-miss 微调
    """Computes the optimal partitions given the size distributions
    and computed number of expected false positives for all sub-intervals.

    Args:
        num_part (int): The number of partitions to create.
        sizes (numpy.array): The complete domain of set sizes in sorted order.
        nfps (numpy.array): The computed number of expected false positives
            for all sub-intervals; axis-0 is for the indexes of lower bounds and
            axis-1 is for the indexes of upper bounds.

    Returns:
        partitions (list): list of lower and upper bounds of set sizes for
            all partitions.
        total_nfps (float): total number of expected false positives from all
            partitions.
        cost (numpy.array): a N x p-1 matrix of the computed optimal NFPs for
            all sub-problems given upper bound set size and number of partitions.

    """
    if num_part < 2:
        raise ValueError("num_part cannot be less than 2")
    if num_part > len(sizes):
        raise ValueError("num_part cannot be greater than the domain size of all set sizes")

    # If number of partitions is 2, then simply find the upper bound
    # of the first partition.
    if num_part == 2:
        total_nfps, u = min((nfps[0, u1] + nfps[u1 + 1, len(sizes) - 1], u1) for u1 in range(0, len(sizes) - 1))
        return (
            [
                (sizes[0], sizes[u]),
                (sizes[u + 1], sizes[-1]),
            ],
            total_nfps,
            None,
        )

    # Initialize subproblem total NFPs.
    cost = np.zeros((len(sizes), num_part - 2))

    # Note: p is the number of partitions in the subproblem.
    # p2i translates the number of partition into the index in the matrix.
    p2i = lambda p: p - 2

    # Compute p >= 2 until before p = num_part.
    for p in range(2, num_part):
        # Compute best partition for subproblems with increasing
        # max index u, starting from the smallest possible u given the p.
        # The smallest possible u can be considered as the max index that
        # generates p partitions each with only one size.
        for u in range(p - 1, len(sizes)):
            if p == 2:
                cost[u, p2i(p)] = min(nfps[0, u1] + nfps[u1 + 1, u] for u1 in range(u))
            else:
                cost[u, p2i(p)] = min(cost[u1, p2i(p - 1)] + nfps[u1 + 1, u] for u1 in range((p - 1) - 1, u))
    p = num_part
    # Find the optimal upper bound index of the 2nd right-most partition given
    # the number of partitions (p).
    total_nfps, u = min(
        (cost[u1, p2i(p - 1)] + nfps[u1 + 1, len(sizes) - 1], u1) for u1 in range((p - 1) - 1, len(sizes) - 1)
    )
    partitions = [
        (sizes[u + 1], sizes[-1]),
    ]
    p -= 1
    # Back track to find the best partitions.
    while p > 1:
        # Find the optimal upper bound index of the 2nd right-most partition
        # givne the number of partitions (p) and upper bound index (u) in this
        # sub-problem.
        _, u1_best = min((cost[u1, p2i(p)] + nfps[u1 + 1, u], u1) for u1 in range((p - 1) - 1, u))
        partitions.insert(0, (sizes[u1_best + 1], sizes[u]))
        u = u1_best
        p -= 1
    partitions.insert(0, (sizes[0], sizes[u]))
    return [partitions, total_nfps, cost]