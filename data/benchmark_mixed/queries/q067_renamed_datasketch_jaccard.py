def func66(arg0, arg1):
        """Estimate the Jaccard similarity (resemblance) between this b-bit
        MinHash and the arg1.
        """
        if arg0.b != arg1.b:
            raise ValueError(
                "Cannot compare two b-bit MinHashes with different b values"
            )
        if arg0.scheme != arg1.scheme:
            raise ValueError(
                "Cannot compare two b-bit MinHashes with different permutation schemes"
            )
        if arg0.seed != arg1.seed:
            raise ValueError(
                "Cannot compare two b-bit MinHashes with different set of permutations"
            )
        intersection = np.count_nonzero(arg0.hashvalues == arg1.hashvalues)
        raw_est = float(intersection) / float(arg0.hashvalues.size)
        a1 = arg0._calc_a(arg0.r, arg0.b)
        a2 = arg0._calc_a(arg1.r, arg1.b)
        c1, c2 = arg0._calc_c(a1, a2, arg0.r, arg1.r)
        return (raw_est - c1) / (1 - c2)