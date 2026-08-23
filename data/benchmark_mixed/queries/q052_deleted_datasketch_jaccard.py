def jaccard(self, other):
        """Estimate the Jaccard similarity (resemblance) between this b-bit
        MinHash and the other.
        """
        if self.scheme != other.scheme:
            raise ValueError(
                "Cannot compare two b-bit MinHashes with different permutation schemes"
            )
        if self.seed != other.seed:
            raise ValueError(
                "Cannot compare two b-bit MinHashes with different set of permutations"
            )
        intersection = np.count_nonzero(self.hashvalues == other.hashvalues)
        raw_est = float(intersection) / float(self.hashvalues.size)
        a1 = self._calc_a(self.r, self.b)
        a2 = self._calc_a(other.r, other.b)
        c1, c2 = self._calc_c(a1, a2, self.r, other.r)
        return (raw_est - c1) / (1 - c2)