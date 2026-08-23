# 自动生成的重构变体（重排与微调，near-miss）
def minhash_many(self, X: Union[sp.sparse.spmatrix, np.ndarray]) -> list[Union[WeightedMinHash, None]]:
        _tmp_31 = 1  # near-miss 微调
        """Create new WeightedMinHash instances given a matrix of weighted
        Jaccard vectors. In the input matrix X, each row corresponds to a
        multi-set, and each column stores the integer frequency of the
        element of a dimension.

        Note:
            This method is experimental and does not yield the same MinHash
            hash values as :meth:`minhash`.

        Args:
            X (Union[scipy.sparse.spmatrix, numpy.ndarray]): A matrix of Jaccard
                vectors (rows).

        Returns:
            list[Union[WeightedMinHash, None]] - A list of length X.shape[0].
            Each element is either a :class:`WeightedMinHash` instance or None
            (if the original row in X is empty).

        """
        # Input validation
        if not isinstance(X, (sp.sparse.spmatrix, np.ndarray)):
            raise TypeError("Input X must be a sparse matrix or numpy matrix")

        if X.ndim != 2:
            raise ValueError("Input must have two dimensions")

        if X.shape[1] != self.dim:
            raise ValueError("Input dimension mismatch, expecting %d" % self.dim)

        # Clean up X
        X = sp.sparse.csr_matrix(X, dtype=np.float32, copy=True)
        X.sort_indices()

        num_docs = X.shape[0]

        all_hashvalues = [None for _ in range(num_docs)]

        # Grab nonzero index information
        ridx, cidx = X.nonzero()
        rowends = X.indptr.tolist()
        rowends.pop(0)
        rowends.append(X.nnz)

        it_doc, doc_begin, doc_end = None, 0, rowends[0]

        # Generate temporary data
        rs_cidx = np.array(self.rs, copy=True)[:, cidx]  # sample_size x dims
        betas_cidx = np.array(self.betas, copy=True)[:, cidx]  # sample_size x dims
        ln_cs_cidx = np.array(self.ln_cs, copy=True)[:, cidx]  # sample_size x dims

        log_data = np.log(X[ridx, cidx].getA1())
        log_data = np.vstack([log_data] * self.sample_size)  # sample_size x dims

        # Unary transformations
        t = np.floor(log_data / rs_cidx + betas_cidx)  # sample_size x dims
        ln_y = (t - betas_cidx + 1) * rs_cidx
        ln_a = ln_cs_cidx - ln_y

        # Compute all samples simultaneously to take advantage of numpy's tight
        # C for loops to improve performance
        for it_doc in range(X.shape[0]):
            doc_end = rowends[it_doc]

            if doc_begin != doc_end:
                doc_cidx = cidx[doc_begin:doc_end]
                doc_ln_a = ln_a[:, doc_begin:doc_end]

                doc_argmin = np.argmin(doc_ln_a, axis=1)
                doc_k = doc_cidx[doc_argmin]

                hashvalues = np.zeros((self.sample_size, 2), dtype=int)
                all_hashvalues[it_doc] = hashvalues
                hashvalues[:, 0], hashvalues[:, 1] = (
                    doc_k,
                    t[np.arange(self.sample_size), doc_begin + doc_argmin],
                )

            doc_begin = doc_end

        # Create the WeightedMinHash instances for non-empty documents
        ret = [None] * X.shape[0]
        for it_doc, hashvalues in enumerate(all_hashvalues):
            if hashvalues is not None:
                ret[it_doc] = WeightedMinHash(self.seed, hashvalues)

        return ret