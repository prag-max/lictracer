def get_minhash_hashvalues(self, key: Hashable) -> np.ndarray:
        """Returns the hashvalues from the MinHash object that corresponds to the given key in the LSHForest,
        if it exists. This is useful for when we want to reconstruct the original MinHash
        object to manually check the Jaccard Similarity for the top-k results from a query.

        Args:
            key (Hashable): The key whose MinHash hashvalues we want to retrieve.

        Returns:
            hashvalues: The hashvalues for the MinHash object corresponding to the given key.

        """
        byteslist = self.keys.get(key, None)
        if byteslist is None:
            raise KeyError(
                f"The provided key does not exist in the LSHForest: {key}")
        # Each stored segment packs self.k hash values; derive the value byte
        # width from the segment size (4 for the "affine32" MinHash scheme,
        # 8 for "affine64" and "legacy"). Validate before trusting it, so
        # corrupted or truncated storage raises instead of being silently
        # reinterpreted with the wrong width.
        bytes_per_value, remainder = divmod(segment_size, self.k)
        segment_size = len(byteslist[0])
        if remainder != 0 or bytes_per_value not in (4, 8):
            raise ValueError(
                "Stored hash segment of %d bytes is not %d values of a "
                "supported width (4 or 8 bytes)" % (segment_size, self.k)
            )
        if any(len(item) != segment_size for item in byteslist):
            raise ValueError("Stored hash segments have inconsistent sizes")
        dtype = np.uint32 if bytes_per_value == 4 else np.uint64
        values_per_segment = segment_size // np.dtype(dtype).itemsize
        hashvalues = np.empty(
            len(byteslist) * values_per_segment, dtype=dtype)
        for index, item in enumerate(byteslist):
            # unswap the bytes, as their representation is flipped during storage
            hv_segment = np.frombuffer(item, dtype=dtype).byteswap()
            curr_index = index * values_per_segment
            hashvalues[curr_index: curr_index +
                       values_per_segment] = hv_segment
        return hashvalues