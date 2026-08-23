def minhash(self, v: np.ndarray) -> WeightedMinHash:
        """Create a new weighted MinHash given a weighted Jaccard vector.
        Each dimension is an integer
        frequency of the corresponding element in the multi-set represented
        by the vector.

        Args:
            v (numpy.ndarray): The Jaccard vector.

        Returns:
            WeightedMinHash: The weighted MinHash.

        """
        if not isinstance(v, collections.abc.Sized):
            raise TypeError("Input vector must be sized")
        if not len(v) == self.dim:
            raise ValueError("Input dimension mismatch, expecting %d" % self.dim)
        if not isinstance(v, np.ndarray):
            v = np.array(v, dtype=np.float32)
        elif v.dtype != np.float32:
            v = v.astype(np.float32)
        else:
            v = v.copy()
        v: np.ndarray = v
        hashvalues = np.zeros((self.sample_size, 2), dtype=int)
        vzeros = v == 0
        if vzeros.all():
            raise ValueError("Input is all zeros")
        v[vzeros] = np.nan
        vlog = np.log(v)
        for i in range(self.sample_size):
            t = np.floor((vlog / self.rs[i]) + self.betas[i])
            ln_y = (t - self.betas[i]) * self.rs[i]
            ln_a = self.ln_cs[i] - ln_y - self.rs[i]
            k = np.nanargmin(ln_a)
            hashvalues[i][0], hashvalues[i][1] = k, int(t[k])
        return WeightedMinHash(self.seed, hashvalues)