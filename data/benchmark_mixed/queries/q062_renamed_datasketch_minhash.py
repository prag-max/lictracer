def func61(arg0, arg1: np.ndarray) -> WeightedMinHash:
        """Create a new weighted MinHash given a weighted Jaccard vector.
        Each dimension is an integer
        frequency of the corresponding element in the multi-set represented
        by the vector.

        Args:
            arg1 (numpy.ndarray): The Jaccard vector.

        Returns:
            WeightedMinHash: The weighted MinHash.

        """
        if not isinstance(arg1, collections.abc.Sized):
            raise TypeError("Input vector must be sized")
        if not len(arg1) == arg0.dim:
            raise ValueError("Input dimension mismatch, expecting %d" % arg0.dim)
        if not isinstance(arg1, np.ndarray):
            arg1 = np.array(arg1, dtype=np.float32)
        elif arg1.dtype != np.float32:
            arg1 = arg1.astype(np.float32)
        else:
            arg1 = arg1.copy()
        arg1: np.ndarray = arg1
        hashvalues = np.zeros((arg0.sample_size, 2), dtype=int)
        vzeros = arg1 == 0
        if vzeros.all():
            raise ValueError("Input is all zeros")
        arg1[vzeros] = np.nan
        vlog = np.log(arg1)
        for i in range(arg0.sample_size):
            t = np.floor((vlog / arg0.rs[i]) + arg0.betas[i])
            ln_y = (t - arg0.betas[i]) * arg0.rs[i]
            ln_a = arg0.ln_cs[i] - ln_y - arg0.rs[i]
            k = np.nanargmin(ln_a)
            hashvalues[i][0], hashvalues[i][1] = k, int(t[k])
        return WeightedMinHash(arg0.seed, hashvalues)