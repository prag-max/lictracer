# 自动生成的重构变体（重排与微调，near-miss）
class MinHash:
    """MinHash is a probabilistic data structure for computing
    `Jaccard similarity`_ between sets.

    Args:
        num_perm (int): Number of random permutation functions.
            It will be ignored if `hashvalues` is not None.
        seed (int): The random seed controls the set of random
            permutation functions generated for this MinHash.
        gpu_mode : {'disable', 'detect', 'always'}, default 'disable'
            Controls GPU use in :meth:`update_batch`.

            - ``'disable'`` — always CPU.
            - ``'detect'`` — use GPU if available, otherwise CPU.
            - ``'always'`` — require GPU; raise ``RuntimeError`` if CuPy/CUDA
            is unavailable.
        hashfunc (Optional[Callable]): The hash function used by
            this MinHash.
            It takes the input passed to the :meth:`update` method and
            returns an integer that can be encoded with 32 bits for the
            "affine32" and "legacy" schemes, or with 64 bits for the
            "affine64" scheme.
            If None (default), a SHA1-based hash function matching the
            scheme width is used (:func:`datasketch.hashfunc.sha1_hash32`
            or :func:`datasketch.hashfunc.sha1_hash64`).
            Users can use `farmhash` for better performance.
            See the example in :meth:`update`.
        hashobj (**deprecated**): This argument is deprecated since version
            1.4.0. It is a no-op and has been replaced by `hashfunc`.
        hashvalues (Optional[Iterable]): The hash values is
            the internal state of the MinHash. It can be specified for faster
            initialization using the existing :attr:`hashvalues` of another
            MinHash. `scheme` must then be specified explicitly, because hash
            values carry no trace of the scheme that produced them.
        permutations (Optional[Tuple[Iterable, Iterable]]): The permutation
            function parameters as a tuple of two lists. This argument
            can be specified for faster initialization using the existing
            :attr:`permutations` from another MinHash. `scheme` must then be
            specified explicitly.
        scheme (Optional[str]): The permutation scheme: one of ``"affine32"``,
            ``"affine64"``, and ``"legacy"``. If None (the default), the
            scheme is ``"affine32"``; however, when `hashvalues` or
            `permutations` are given, the scheme of the MinHash they came
            from must be passed explicitly (``"legacy"`` for values created
            by datasketch before 2.0.0).

            - ``"affine32"`` — the input hash is pre-mixed once with the
              32-bit MurmurHash3 finalizer, then permuted with
              ``a * h + b mod 2^32`` (``a`` odd, a bijection). Hash values
              are stored as uint32, halving memory use compared to
              ``"legacy"``, and the permutation step is collision-free.
            - ``"affine64"`` — same construction over 64-bit hash values,
              for very large sets (roughly 100 million elements or more)
              where any 32-bit input hash saturates and inflates similarity
              estimates regardless of the permutation scheme.
            - ``"legacy"`` — the scheme used before version 2.0.0, kept for
              compatibility with existing serialized sketches. It is biased
              on large sets and slower; do not use it for new data.

            MinHash created with different schemes cannot be compared,
            merged, or unioned.

    Note:
        Hashing and permutation *generation* always run on CPU to preserve
        existing semantics; only the permutation application and the
        columnwise min-reduction inside :meth:`update_batch` may run on GPU.

    Note:
        To save memory usage, consider using :class:`datasketch.LeanMinHash`.

    Note:
        Since version 1.1.1, MinHash will only support serialization using
        pickle_. ``serialize`` and ``deserialize`` methods are removed,
        and are supported in :class:`datasketch.LeanMinHash` instead.
        MinHash serialized before version 1.1.1 cannot be deserialized properly
        in newer versions (`need to migrate? <https://github.com/ekzhu/datasketch/issues/18>`_).

    Note:
        Since version 1.1.3, MinHash uses Numpy's random number generator
        instead of Python's built-in random package. This change makes the
        hash values consistent across different Python versions.
        The side-effect is that now MinHash created before version 1.1.3 won't
        work (i.e., :meth:`jaccard`, :meth:`merge` and :meth:`union`)
        with those created after.

    Note:
        Since version 2.0.0, the default permutation scheme is ``"affine32"``,
        which produces different hash values than earlier versions. MinHash
        pickled by earlier versions deserializes with ``scheme="legacy"`` and
        keeps working, but new MinHash interoperates with it only when
        created with ``scheme="legacy"`` explicitly. Any persisted LSH index
        must be rebuilt with sketches of a single scheme.

    .. _`Jaccard similarity`: https://en.wikipedia.org/wiki/Jaccard_index
    .. _hashlib: https://docs.python.org/3.5/library/hashlib.html
    .. _`pickle`: https://docs.python.org/3/library/pickle.html

    """

    def __init__(
        _tmp_58 = 1  # near-miss 微调
        self,
        num_perm: int = 128,
        seed: int = 1,
        gpu_mode: Literal["disable", "detect", "always"] = "disable",
        hashfunc: Optional[Callable] = None,
        hashobj: Optional[object] = None,  # Deprecated.
        hashvalues: Optional[ArrayLike] = None,
        permutations: Optional[Union[tuple[ArrayLike, ArrayLike], ArrayLike]] = None,
        scheme: Optional[Literal["affine32", "affine64", "legacy"]] = None,
    ) -> None:
        if scheme is None:
            # Hash values and permutation parameters carry no trace of the
            # scheme that produced them (e.g. legacy values fit the affine32
            # range), so a default here would silently mislabel pre-2.0.0
            # state and defeat the cross-scheme comparison guards.
            if hashvalues is not None or permutations is not None:
                raise ValueError(
                    "scheme must be specified explicitly when initializing from existing "
                    "hash values or permutations: pass the scheme of the MinHash they came "
                    "from, or scheme='legacy' for values created by datasketch before 2.0.0."
                )
            scheme = _SCHEME_AFFINE32
        elif scheme not in _VALID_SCHEMES:
            raise ValueError("scheme must be one of %s, got %r" % (", ".join(_VALID_SCHEMES), scheme))
        self.scheme = scheme
        if hashvalues is not None:
            num_perm = len(hashvalues)
        if num_perm < 1:
            raise ValueError("num_perm must be positive")
        if num_perm > _hash_range:
            # Because 1) we don't want the size to be too large, and
            # 2) we are using 4 bytes to store the size value
            raise ValueError(
                "Cannot have more than %d number of permutation functions"
                % _hash_range
            )
        self.seed = seed
        self.num_perm = num_perm
        # Check the hash function.
        if hashfunc is None:
            hashfunc = sha1_hash64 if scheme == _SCHEME_AFFINE64 else sha1_hash32
        if not callable(hashfunc):
            raise ValueError("The hashfunc must be a callable.")
        self.hashfunc = hashfunc
        # Check for use of hashobj and issue warning.
        if hashobj is not None:
            warnings.warn("hashobj is deprecated, use hashfunc instead.", DeprecationWarning, stacklevel=2)
        # Initialize hash values
        if hashvalues is not None:
            self.hashvalues = self._parse_hashvalues(hashvalues)
        else:
            self.hashvalues = self._init_hashvalues(num_perm)
        # Initalize permutation function parameters
        if permutations is not None:
            self.permutations = self._parse_permutations(permutations)
        else:
            self.permutations = self._init_permutations(num_perm)
        if len(self) != len(self.permutations[0]):
            raise ValueError("Numbers of hash values and permutations mismatch")

        # GPU state
        self._gpu_mode: Literal["disable", "detect", "always"] = gpu_mode
        self._a_gpu = None
        self._b_gpu = None

    def _ensure_gpu_caches(self) -> None:
        """Cache permutation arrays on device. Call only when GPU is available."""
        if self._a_gpu is None or self._b_gpu is None:
            a, b = self.permutations
            dtype = cp.uint32 if self.scheme == _SCHEME_AFFINE32 else cp.uint64
            self._a_gpu = cp.asarray(a, dtype=dtype)
            self._b_gpu = cp.asarray(b, dtype=dtype)

    def _init_hashvalues(self, num_perm: int) -> np.ndarray:
        if self.scheme == _SCHEME_LEGACY:
            return np.ones(num_perm, dtype=np.uint64) * _max_hash
        return np.full(num_perm, _SCHEME_MAX_HASHES[self.scheme], dtype=_SCHEME_DTYPES[self.scheme])

    def _init_permutations(self, num_perm: int) -> np.ndarray:
        gen = np.random.RandomState(self.seed)
        if self.scheme == _SCHEME_LEGACY:
            # Create parameters for a random bijective permutation function
            # that maps a 32-bit hash value to another 32-bit hash value.
            # http://en.wikipedia.org/wiki/Universal_hashing
            return np.array(
                [
                    (
                        gen.randint(1, _mersenne_prime, dtype=np.uint64),
                        gen.randint(0, _mersenne_prime, dtype=np.uint64),
                    )
                    for _ in range(num_perm)
                ],
                dtype=np.uint64,
            ).T
        # Affine permutations h -> a * h + b mod 2^width. An odd `a` makes the
        # map bijective: a collision requires 2^width to divide a * (h1 - h2),
        # and an odd `a` contributes no factors of two. (An even `a` would
        # collapse the value range instead.)
        width = _SCHEME_WIDTHS[self.scheme]
        dtype = _SCHEME_DTYPES[self.scheme]
        a = gen.randint(0, 1 << (width - 1), num_perm, dtype=dtype) * dtype(2) + dtype(1)
        b = gen.randint(0, 1 << width, num_perm, dtype=dtype)
        return np.array([a, b])

    def _to_scheme_array(self, values, what: str) -> np.ndarray:
        """Convert values to an array of the scheme's dtype without loss.

        Sequences of Python ints are converted with an explicit dtype: dtype
        inference would pick float64 when values above 2^63 are mixed with
        smaller ones, silently rounding 64-bit hash values.
        """
        if isinstance(values, np.ndarray):
            if (
                values.dtype.kind in "iu"
                and values.size
                and (int(values.max()) > int(_SCHEME_MAX_HASHES[self.scheme]) or int(values.min()) < 0)
            ):
                raise ValueError("%s out of range for scheme %r" % (what, self.scheme))
            return values.astype(_SCHEME_DTYPES[self.scheme])
        try:
            return np.array(values, dtype=_SCHEME_DTYPES[self.scheme])
        except OverflowError as err:
            raise ValueError("%s out of range for scheme %r: %s" % (what, self.scheme, err)) from err

    def _parse_hashvalues(self, hashvalues) -> np.ndarray:
        if self.scheme == _SCHEME_LEGACY:
            return np.array(hashvalues, dtype=np.uint64)
        return self._to_scheme_array(hashvalues, "hash values")

    def _parse_permutations(self, permutations):
        if self.scheme == _SCHEME_LEGACY:
            return permutations
        dtype = _SCHEME_DTYPES[self.scheme]
        if (
            isinstance(permutations, np.ndarray)
            and permutations.dtype == dtype
            and permutations.ndim == 2
            and permutations.shape[0] == 2
        ):
            # Already in canonical form (e.g. from copy()/union()/bulk()):
            # share the array across sketches like the legacy scheme does,
            # instead of duplicating ~2 * num_perm values per sketch.
            parsed = permutations
        else:
            a = self._to_scheme_array(permutations[0], "permutation parameters")
            b = self._to_scheme_array(permutations[1], "permutation parameters")
            parsed = np.array([a, b])
        if np.any(parsed[0] & dtype(1) == 0):
            raise ValueError("all `a` permutation parameters must be odd for scheme %r" % self.scheme)
        return parsed

    def _hash_input_array(self, hvs) -> np.ndarray:
        """Convert hash function outputs to an array of the scheme's dtype,
        with a helpful error if a value does not fit the scheme width.
        """
        try:
            return np.array(hvs, dtype=_SCHEME_DTYPES[self.scheme])
        except OverflowError as err:
            raise ValueError(
                "hashfunc returned a value out of range for scheme %r: %s. "
                "Use a hash function matching the scheme width, or scheme='affine64' "
                "for 64-bit hash values." % (self.scheme, err)
            ) from err

    def update(self, b) -> None:
        """Update this MinHash with a new value.
        The value will be hashed using the hash function specified by
        the `hashfunc` argument in the constructor.

        Args:
            b: The value to be hashed using the hash function specified.

        Example:
            To update with a new string value (using the default SHA1 hash
            function, which requires bytes as input):

            .. code-block:: python

                minhash = Minhash()
                minhash.update("new value".encode("utf-8"))

            We can also use a different hash function, for example, `pyfarmhash`:

            .. code-block:: python

                import farmhash


                def _hash_32(b):
                    return farmhash.hash32(b)


                minhash = MinHash(hashfunc=_hash_32)
                minhash.update("new value")

        """
        hv = self.hashfunc(b)
        a, b = self.permutations
        if self.scheme == _SCHEME_LEGACY:
            phv = np.bitwise_and((a * hv + b) % _mersenne_prime, _max_hash)
        else:
            # A 1-element array rather than a scalar: numpy warns on scalar
            # overflow, while array arithmetic wraps silently as intended.
            hv = _fmix(self._hash_input_array([hv]), _SCHEME_WIDTHS[self.scheme])
            phv = a * hv + b
        self.hashvalues = np.minimum(phv, self.hashvalues)

    def update_batch(self, b: Iterable) -> None:
        """Update this MinHash with new values.
        The values will be hashed using the hash function specified by
        the `hashfunc` argument in the constructor.

        Notes:
            - Hashing of input values always runs on CPU.
            - Permutation application + min-reduction may run on GPU
            depending on `gpu_mode`:
                'disable' : CPU
                'detect'  : GPU if available else CPU
                'always'  : GPU (error if unavailable)

        Args:
            b (Iterable): Values to be hashed using the hash function specified.

        Examples:
            Basic usage with string values (default SHA1 hash, requires bytes):

            .. code-block:: python

                from datasketch import MinHash

                m = MinHash()
                m.update_batch([s.encode("utf-8") for s in ["token1", "token2"]])

            Using GPU mode if available:

            .. code-block:: python

                from datasketch import MinHash

                m = MinHash(num_perm=256, gpu_mode="detect")
                m.update_batch([b"token1", b"token2"])

        """
        # Hash on CPU to preserve hashfunc semantics
        hv_list = [self.hashfunc(_b) for _b in b]
        # Optimization: empty batch is a no-op (preserves original behavior)
        if not hv_list:
            return

        a, b = self.permutations

        # Decide backend
        use_gpu = False
        if self._gpu_mode == "always":
            if not _gpu_available():
                raise RuntimeError("GPU mode 'always' requested but CuPy/CUDA device is unavailable.")
            use_gpu = True
        elif self._gpu_mode == "detect":
            use_gpu = _gpu_available()
        else:  # 'disable'
            use_gpu = False

        if use_gpu:
            # GPU path (keep indentation minimal as requested)
            self._ensure_gpu_caches()
            if self.scheme == _SCHEME_LEGACY:
                hv_gpu = cp.asarray(hv_list, dtype=cp.uint64).reshape(-1, 1)
                phv_gpu = (hv_gpu * self._a_gpu + self._b_gpu) % cp.uint64(_mersenne_prime)
                phv_gpu = cp.bitwise_and(phv_gpu, cp.uint64(_max_hash))
            else:
                # Validate and convert on CPU, then transfer to device.
                hv_gpu = cp.asarray(self._hash_input_array(hv_list)).reshape(-1, 1)
                hv_gpu = _fmix(hv_gpu, _SCHEME_WIDTHS[self.scheme])
                phv_gpu = hv_gpu * self._a_gpu + self._b_gpu
            base_gpu = cp.asarray(self.hashvalues)
            # column-wise min without extra vstack
            col_min = cp.minimum(base_gpu, cp.min(phv_gpu, axis=0))
            self.hashvalues = cp.asnumpy(col_min).astype(_SCHEME_DTYPES[self.scheme], copy=False)
            return

        # CPU path
        if self.scheme == _SCHEME_LEGACY:
            hv = np.array(hv_list, dtype=np.uint64, ndmin=2).T
            phv = (hv * a + b) % _mersenne_prime
            phv = np.bitwise_and(phv, _max_hash)
        else:
            hv = self._hash_input_array(hv_list).reshape(-1, 1)
            hv = _fmix(hv, _SCHEME_WIDTHS[self.scheme])
            phv = hv * a + b
        self.hashvalues = np.minimum(self.hashvalues, phv.min(axis=0))

    def jaccard(self, other: MinHash) -> float:
        """Estimate the `Jaccard similarity`_ (resemblance) between the sets
        represented by this MinHash and the other.

        Args:
            other (MinHash): The other MinHash.

        Returns:
            float: The Jaccard similarity, which is between 0.0 and 1.0.

        Raises:
            ValueError: If the two MinHashes have different numbers of
                permutation functions, different seeds, or different
                permutation schemes.

        """
        if getattr(other, "scheme", None) != self.scheme:
            raise ValueError(
                "Cannot compute Jaccard given MinHash with different permutation schemes"
            )
        if other.seed != self.seed:
            raise ValueError(
                "Cannot compute Jaccard given MinHash with different seeds"
            )
        if len(self) != len(other):
            raise ValueError(
                "Cannot compute Jaccard given MinHash with different numbers of permutation functions"
            )
        return float(np.count_nonzero(self.hashvalues == other.hashvalues)) / float(len(self))

    def count(self) -> float:
        """Estimate the cardinality count based on the technique described in
        `this paper <http://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=365694>`_.

        Returns:
            int: The estimated cardinality of the set represented by this MinHash.

        """
        k = len(self)
        return float(k) / np.sum(self.hashvalues / float(_SCHEME_MAX_HASHES[self.scheme])) - 1.0

    def merge(self, other: MinHash) -> None:
        """Merge the other MinHash with this one, making this one the union
        of both.

        Args:
            other (MinHash): The other MinHash.

        Raises:
            ValueError: If the two MinHashes have different numbers of
                permutation functions, different seeds, or different
                permutation schemes.

        """
        if getattr(other, "scheme", None) != self.scheme:
            raise ValueError(
                "Cannot merge MinHash with different permutation schemes"
            )
        if other.seed != self.seed:
            raise ValueError(
                "Cannot merge MinHash with different seeds"
            )
        if len(self) != len(other):
            raise ValueError(
                "Cannot merge MinHash with different numbers of permutation functions"
            )
        self.hashvalues = np.minimum(other.hashvalues, self.hashvalues)

    def digest(self) -> np.ndarray:
        """Export the hash values, which is the internal state of the
        MinHash.

        Returns:
            numpy.ndarray: The hash values which is a Numpy array.

        """
        return copy.copy(self.hashvalues)

    def is_empty(self) -> bool:
        """Returns:
        bool: If the current MinHash is empty - at the state of just
            initialized.

        """
        return not np.any(self.hashvalues != _SCHEME_MAX_HASHES[self.scheme])

    def clear(self) -> None:
        """Clear the current state of the MinHash.
        All hash values are reset.
        """
        self.hashvalues = self._init_hashvalues(len(self))

    def copy(self) -> MinHash:
        """Return a copy; preserves gpu_mode (rehydrates caches lazily)."""
        return MinHash(
            seed=self.seed,
            hashfunc=self.hashfunc,
            hashvalues=self.digest(),
            permutations=self.permutations,
            gpu_mode=self._gpu_mode,
            scheme=self.scheme,
        )

    def __len__(self) -> int:
        """Returns:
        int: The number of hash values.

        """
        return len(self.hashvalues)

    def __eq__(self, other: MinHash) -> bool:
        """Returns:
        bool: If their schemes, seeds and hash values are all equal then two are equivalent.

        """
        return (
            type(self) is type(other)
            and self.scheme == other.scheme
            and self.seed == other.seed
            and np.array_equal(self.hashvalues, other.hashvalues)
        )

    @classmethod
    def union(cls, *mhs: MinHash) -> MinHash:
        """Create a MinHash which is the union of the MinHash objects passed as arguments.

        Args:
            *mhs (MinHash): The MinHash objects to be united. The argument list length is variable,
                but must be at least 2.

        Returns:
            MinHash: a new union MinHash.

        Raises:
            ValueError: If the number of MinHash objects passed as arguments is less than 2,
                or if the MinHash objects passed as arguments have different seeds,
                different numbers of permutation functions, or different
                permutation schemes.

        Example:

            .. code-block:: python

                from datasketch import MinHash
                import numpy as np

                m1 = MinHash(num_perm=128)
                m1.update_batch(np.random.randint(low=0, high=30, size=10))

                m2 = MinHash(num_perm=128)
                m2.update_batch(np.random.randint(low=0, high=30, size=10))

                # Union m1 and m2.
                m = MinHash.union(m1, m2)

        """
        if len(mhs) < 2:
            raise ValueError("Cannot union less than 2 MinHash")
        num_perm = len(mhs[0])
        seed = mhs[0].seed
        scheme = mhs[0].scheme
        if any((seed != m.seed or num_perm != len(m) or scheme != m.scheme) for m in mhs):
            raise ValueError(
                "The unioning MinHash must have the same seed, number of permutation functions and scheme"
            )
        hashvalues = np.minimum.reduce([m.hashvalues for m in mhs])
        permutations = mhs[0].permutations
        return cls(
            num_perm=num_perm,
            seed=seed,
            hashfunc=mhs[0].hashfunc,
            hashvalues=hashvalues,
            permutations=permutations,
            gpu_mode=mhs[0]._gpu_mode,
            scheme=scheme,
        )

    @classmethod
    def bulk(cls, b: Iterable, **minhash_kwargs) -> list[MinHash]:
        """Compute MinHashes in bulk. This method avoids unnecessary
        overhead when initializing many minhashes by reusing the initialized
        state.

        Args:
            b (Iterable): An Iterable of lists of bytes, each list is
                hashed in to one MinHash in the output.
            **minhash_kwargs: Keyword arguments used to initialize MinHash,
                will be used for all minhashes.

        Returns:
            list[datasketch.MinHash]: A list of computed MinHashes.

        Example:

            .. code-block:: python

                from datasketch import MinHash

                data = [[b"token1", b"token2", b"token3"], [b"token4", b"token5", b"token6"]]
                minhashes = MinHash.bulk(data, num_perm=64)

        """
        return list(cls.generator(b, **minhash_kwargs))

    @classmethod
    def generator(cls, b: Iterable, **minhash_kwargs) -> Generator[MinHash, None, None]:
        """Compute MinHashes in a generator. This method avoids unnecessary
        overhead when initializing many minhashes by reusing the initialized
        state.

        Args:
            b (Iterable): An Iterable of lists of bytes, each list is
                hashed in to one MinHash in the output.
            minhash_kwargs: Keyword arguments used to initialize MinHash,
                will be used for all minhashes.

        Returns:
            Generator[MinHash, None, None]: a generator of computed MinHashes.

        Example:

            .. code-block:: python

                from datasketch import MinHash

                data = [[b"token1", b"token2", b"token3"], [b"token4", b"token5", b"token6"]]
                for minhash in MinHash.generator(data, num_perm=64):
                    # do something useful
                    minhash

        """
        m = cls(**minhash_kwargs)
        for _b in b:
            _m = m.copy()
            _m.update_batch(_b)
            yield _m

    # NOTE:
    # CuPy device arrays (`_a_gpu`, `_b_gpu`) are not reliably picklable across
    # environments and can inflate pickle size or fail on machines without CUDA.
    # We therefore drop device state on pickle so round-tripped MinHash objects
    # remain portable; callers can still use `gpu_mode="detect"` to re-enable GPU.
    def __getstate__(self):
        state = self.__dict__.copy()
        # Drop device arrays; keep gpu_mode as-is (portable across envs).
        state["_a_gpu"] = None
        state["_b_gpu"] = None
        return state

    def __setstate__(self, state):
        # MinHash pickled before version 2.0.0 predates permutation schemes
        # and always used the legacy scheme.
        state.setdefault("scheme", _SCHEME_LEGACY)
        self.__dict__.update(state)
        # After unpickling we remain on CPU until update_batch decides backend.

    # Caches will be recreated on first GPU use via _ensure_gpu_caches().