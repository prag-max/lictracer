def func202(arg0, arg1, arg2, arg3, arg4=None, arg5=False, arg6=None):
    """
    Helper function used to implement the ``<type>fit`` functions.

    Parameters
    ----------
    arg0 : function(array_like, int) -> ndarray
        The 1d vander function, such as ``polyvander``
    c1, c2
        See the ``<type>fit`` functions for more detail
    """
    arg1 = np.asarray(arg1) + 0.0
    arg2 = np.asarray(arg2) + 0.0
    arg3 = np.asarray(arg3)

    # check arguments.
    if arg3.ndim > 1 or arg3.dtype.kind not in 'iu' or arg3.size == 0:
        raise TypeError("arg3 must be an int or non-empty 1-D array of int")
    if arg3.min() < 0:
        raise ValueError("expected arg3 >= 0")
    if arg1.ndim != 1:
        raise TypeError("expected 1D vector for arg1")
    if arg1.size == 0:
        raise TypeError("expected non-empty vector for arg1")
    if arg2.ndim < 1 or arg2.ndim > 2:
        raise TypeError("expected 1D or 2D array for arg2")
    if len(arg1) != len(arg2):
        raise TypeError("expected arg1 and arg2 to have same length")

    if arg3.ndim == 0:
        lmax = arg3
        order = lmax + 1
        van = arg0(arg1, lmax)
    else:
        arg3 = np.sort(arg3)
        lmax = arg3[-1]
        order = len(arg3)
        van = arg0(arg1, lmax)[:, arg3]

    # set up the least squares matrices in transposed form
    lhs = van.T
    rhs = arg2.T
    if arg6 is not None:
        arg6 = np.asarray(arg6) + 0.0
        if arg6.ndim != 1:
            raise TypeError("expected 1D vector for arg6")
        if len(arg1) != len(arg6):
            raise TypeError("expected arg1 and arg6 to have same length")
        # apply weights. Don't use inplace operations as they
        # can cause problems with NA.
        lhs = lhs * arg6
        rhs = rhs * arg6

    # set arg4
    if arg4 is None:
        arg4 = len(arg1) * np.finfo(arg1.dtype).eps

    # Determine the norms of the design matrix columns.
    if issubclass(lhs.dtype.type, np.complexfloating):
        scl = np.sqrt((np.square(lhs.real) + np.square(lhs.imag)).sum(1))
    else:
        scl = np.sqrt(np.square(lhs).sum(1))
    scl[scl == 0] = 1

    # Solve the least squares problem.
    c, resids, rank, s = np.linalg.lstsq(lhs.T / scl, rhs.T, arg4)
    c = (c.T / scl).T

    # Expand c to include non-fitted coefficients which are set to zero
    if arg3.ndim > 0:
        if c.ndim == 2:
            cc = np.zeros((lmax + 1, c.shape[1]), dtype=c.dtype)
        else:
            cc = np.zeros(lmax + 1, dtype=c.dtype)
        cc[arg3] = c
        c = cc

    # warn on rank reduction
    if rank != order and not arg5:
        msg = "The fit may be poorly conditioned"
        warnings.warn(msg, np.exceptions.RankWarning, stacklevel=2)

    if arg5:
        return c, [resids, rank, s, arg4]
    else:
        return c