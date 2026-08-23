def func76(arg0, arg1: Iterable) -> None:
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
            arg1 (Iterable): Values to be hashed using the hash function specified.

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
                m.update_batch([arg1"token1", arg1"token2"])

        """
        # Hash on CPU to preserve hashfunc semantics
        hv_list = [arg0.hashfunc(_b) for _b in arg1]
        # Optimization: empty batch is a no-op (preserves original behavior)
        if not hv_list:
            return

        a, arg1 = arg0.permutations

        # Decide backend
        use_gpu = False
        if arg0._gpu_mode == "always":
            if not _gpu_available():
                raise RuntimeError("GPU mode 'always' requested but CuPy/CUDA device is unavailable.")
            use_gpu = True
        elif arg0._gpu_mode == "detect":
            use_gpu = _gpu_available()
        else:  # 'disable'
            use_gpu = False

        if use_gpu:
            # GPU path (keep indentation minimal as requested)
            arg0._ensure_gpu_caches()
            if arg0.scheme == _SCHEME_LEGACY:
                hv_gpu = cp.asarray(hv_list, dtype=cp.uint64).reshape(-1, 1)
                phv_gpu = (hv_gpu * arg0._a_gpu + arg0._b_gpu) % cp.uint64(_mersenne_prime)
                phv_gpu = cp.bitwise_and(phv_gpu, cp.uint64(_max_hash))
            else:
                # Validate and convert on CPU, then transfer to device.
                hv_gpu = cp.asarray(arg0._hash_input_array(hv_list)).reshape(-1, 1)
                hv_gpu = _fmix(hv_gpu, _SCHEME_WIDTHS[arg0.scheme])
                phv_gpu = hv_gpu * arg0._a_gpu + arg0._b_gpu
            base_gpu = cp.asarray(arg0.hashvalues)
            # column-wise min without extra vstack
            col_min = cp.minimum(base_gpu, cp.min(phv_gpu, axis=0))
            arg0.hashvalues = cp.asnumpy(col_min).astype(_SCHEME_DTYPES[arg0.scheme], copy=False)
            return

        # CPU path
        if arg0.scheme == _SCHEME_LEGACY:
            hv = np.array(hv_list, dtype=np.uint64, ndmin=2).T
            phv = (hv * a + arg1) % _mersenne_prime
            phv = np.bitwise_and(phv, _max_hash)
        else:
            hv = arg0._hash_input_array(hv_list).reshape(-1, 1)
            hv = _fmix(hv, _SCHEME_WIDTHS[arg0.scheme])
            phv = hv * a + arg1
        arg0.hashvalues = np.minimum(arg0.hashvalues, phv.min(axis=0))