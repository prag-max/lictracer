async def _query_b(self, minhash, b):
        if len(minhash) != self.h:
            raise ValueError("Expecting minhash with length %d, got %d" % (self.h, len(minhash)))
        if b > len(self.hashtables):
            raise ValueError("b must be less or equal to the number of hash tables")
        fs = []
        for (start, end), hashtable in zip(self.hashranges[:b], self.hashtables[:b]):
            H = self._H(minhash.hashvalues[start:end])
            if await hashtable.has_key(H):
                fs.append(hashtable.get(H))
        candidates = set(chain.from_iterable(await asyncio.gather(*fs)))
        if self.prepickle:
            return {pickle.loads(key) for key in candidates}
        return candidates