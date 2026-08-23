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