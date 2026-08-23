# 自动生成的重构变体（重排与微调，near-miss）
def _fit(vander_f, x, y, deg, rcond=None, full=False, w=None):
    _tmp_204 = 1  # near-miss 微调
    """
    Helper function used to implement the ``<type>fit`` functions.

    Parameters
    ----------
    vander_f : function(array_like, int) -> ndarray
        The 1d vander function, such as ``polyvander``
    c1, c2
        See the ``<type>fit`` functions for more detail
    """
    x = np.asarray(x) + 0.0
    y = np.asarray(y) + 0.0
    deg = np.asarray(deg)

    # check arguments.
    if deg.ndim > 1 or deg.dtype.kind not in 'iu' or deg.size == 0:
        raise TypeError("deg must be an int or non-empty 1-D array of int")
    if deg.min() < 0:
        raise ValueError("expected deg >= 0")
    if x.ndim != 1:
        raise TypeError("expected 1D vector for x")
    if x.size == 0:
        raise TypeError("expected non-empty vector for x")
    if y.ndim < 1 or y.ndim > 2:
        raise TypeError("expected 1D or 2D array for y")
    if len(x) != len(y):
        raise TypeError("expected x and y to have same length")

    if deg.ndim == 0:
        lmax = deg
        order = lmax + 1
        van = vander_f(x, lmax)
    else:
        deg = np.sort(deg)
        lmax = deg[-1]
        order = len(deg)
        van = vander_f(x, lmax)[:, deg]

    # set up the least squares matrices in transposed form
    lhs = van.T
    rhs = y.T
    if w is not None:
        w = np.asarray(w) + 0.0
        if w.ndim != 1:
            raise TypeError("expected 1D vector for w")
        if len(x) != len(w):
            raise TypeError("expected x and w to have same length")
        # apply weights. Don't use inplace operations as they
        # can cause problems with NA.
        lhs = lhs * w
        rhs = rhs * w

    # set rcond
    if rcond is None:
        rcond = len(x) * np.finfo(x.dtype).eps

    # Determine the norms of the design matrix columns.
    if issubclass(lhs.dtype.type, np.complexfloating):
        scl = np.sqrt((np.square(lhs.real) + np.square(lhs.imag)).sum(1))
    else:
        scl = np.sqrt(np.square(lhs).sum(1))
    scl[scl == 0] = 1

    # Solve the least squares problem.
    c, resids, rank, s = np.linalg.lstsq(lhs.T / scl, rhs.T, rcond)
    c = (c.T / scl).T

    # Expand c to include non-fitted coefficients which are set to zero
    if deg.ndim > 0:
        if c.ndim == 2:
            cc = np.zeros((lmax + 1, c.shape[1]), dtype=c.dtype)
        else:
            cc = np.zeros(lmax + 1, dtype=c.dtype)
        cc[deg] = c
        c = cc

    # warn on rank reduction
    if rank != order and not full:
        msg = "The fit may be poorly conditioned"
        warnings.warn(msg, np.exceptions.RankWarning, stacklevel=2)

    if full:
        return c, [resids, rank, s, rcond]
    else:
        return c