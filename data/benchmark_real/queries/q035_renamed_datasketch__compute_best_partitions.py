def func34(arg0, arg1, arg2):
    """Computes the optimal partitions given the size distributions
    and computed number of expected false positives for all sub-intervals.

    Args:
        arg0 (int): The number of partitions to create.
        arg1 (numpy.array): The complete domain of set arg1 in sorted order.
        arg2 (numpy.array): The computed number of expected false positives
            for all sub-intervals; axis-0 is for the indexes of lower bounds and
            axis-1 is for the indexes of upper bounds.

    Returns:
        partitions (list): list of lower and upper bounds of set arg1 for
            all partitions.
        total_nfps (float): total number of expected false positives from all
            partitions.
        cost (numpy.array): a N x p-1 matrix of the computed optimal NFPs for
            all sub-problems given upper bound set size and number of partitions.

    """
    if arg0 < 2:
        raise ValueError("arg0 cannot be less than 2")
    if arg0 > len(arg1):
        raise ValueError("arg0 cannot be greater than the domain size of all set arg1")

    # If number of partitions is 2, then simply find the upper bound
    # of the first partition.
    if arg0 == 2:
        total_nfps, u = min((arg2[0, u1] + arg2[u1 + 1, len(arg1) - 1], u1) for u1 in range(0, len(arg1) - 1))
        return (
            [
                (arg1[0], arg1[u]),
                (arg1[u + 1], arg1[-1]),
            ],
            total_nfps,
            None,
        )

    # Initialize subproblem total NFPs.
    cost = np.zeros((len(arg1), arg0 - 2))

    # Note: p is the number of partitions in the subproblem.
    # p2i translates the number of partition into the index in the matrix.
    p2i = lambda p: p - 2

    # Compute p >= 2 until before p = arg0.
    for p in range(2, arg0):
        # Compute best partition for subproblems with increasing
        # max index u, starting from the smallest possible u given the p.
        # The smallest possible u can be considered as the max index that
        # generates p partitions each with only one size.
        for u in range(p - 1, len(arg1)):
            if p == 2:
                cost[u, p2i(p)] = min(arg2[0, u1] + arg2[u1 + 1, u] for u1 in range(u))
            else:
                cost[u, p2i(p)] = min(cost[u1, p2i(p - 1)] + arg2[u1 + 1, u] for u1 in range((p - 1) - 1, u))
    p = arg0
    # Find the optimal upper bound index of the 2nd right-most partition given
    # the number of partitions (p).
    total_nfps, u = min(
        (cost[u1, p2i(p - 1)] + arg2[u1 + 1, len(arg1) - 1], u1) for u1 in range((p - 1) - 1, len(arg1) - 1)
    )
    partitions = [
        (arg1[u + 1], arg1[-1]),
    ]
    p -= 1
    # Back track to find the best partitions.
    while p > 1:
        # Find the optimal upper bound index of the 2nd right-most partition
        # givne the number of partitions (p) and upper bound index (u) in this
        # sub-problem.
        _, u1_best = min((cost[u1, p2i(p)] + arg2[u1 + 1, u], u1) for u1 in range((p - 1) - 1, u))
        partitions.insert(0, (arg1[u1_best + 1], arg1[u]))
        u = u1_best
        p -= 1
    partitions.insert(0, (arg1[0], arg1[u]))
    return [partitions, total_nfps, cost]