def _minimize_lbfgsb(fun, x0, args=(), jac=None, bounds=None, maxcor=10,
                     ftol=2.2204460492503131e-09, gtol=1e-5, eps=1e-8, maxfun=15000,
                     maxiter=15000, callback=None, maxls=20, finite_diff_rel_step=None,
                     workers=None, **unknown_options):
    """
    Minimize a scalar function of one or more variables using the L-BFGS-B
    algorithm.

    Options
    -------
    maxcor : int
        The maximum number of variable metric corrections used to
        define the limited memory matrix. (The limited memory BFGS
        method does not store the full hessian but uses this many terms
        in an approximation to it.)
    ftol : float
        The iteration stops when ``(f^k -
        f^{k+1})/max{|f^k|,|f^{k+1}|,1} <= ftol``.
    gtol : float
        The iteration will stop when ``max{|proj g_i | i = 1, ..., n}
        <= gtol`` where ``proj g_i`` is the i-th component of the
        projected gradient.
    eps : float or ndarray
        If `jac is None` the absolute step size used for numerical
        approximation of the jacobian via forward differences.
    maxfun : int
        Maximum number of function evaluations before minimization terminates.
        Note that this function may violate the limit if the gradients
        are evaluated by numerical differentiation.
    maxiter : int
        Maximum number of algorithm iterations.
    maxls : int, optional
        Maximum number of line search steps (per iteration). Default is 20.
    finite_diff_rel_step : None or array_like, optional
        If ``jac in ['2-point', '3-point', 'cs']`` the relative step size to
        use for numerical approximation of the jacobian. The absolute step
        size is computed as ``h = rel_step * sign(x) * max(1, abs(x))``,
        possibly adjusted to fit into the bounds. For ``method='3-point'``
        the sign of `h` is ignored. If None (default) then step is selected
        automatically.
    workers : int, map-like callable, optional
        A map-like callable, such as `multiprocessing.Pool.map` for evaluating
        any numerical differentiation in parallel.
        This evaluation is carried out as ``workers(fun, iterable)``.

        .. versionadded:: 1.16.0

    Notes
    -----
    The option `ftol` is exposed via the `scipy.optimize.minimize` interface,
    but calling `scipy.optimize.fmin_l_bfgs_b` directly exposes `factr`. The
    relationship between the two is ``ftol = factr * numpy.finfo(float).eps``.
    I.e., `factr` multiplies the default machine floating-point precision to
    arrive at `ftol`.
    If the minimization is slow to converge the optimizer may halt if the
    total number of function evaluations exceeds `maxfun`, or the number of
    algorithm iterations has reached `maxiter` (whichever comes first). If
    this is the case then ``result.success=False``, and an appropriate
    error message is contained in ``result.message``.

    """
    _check_unknown_options(unknown_options)
    m = maxcor
    factr = ftol / np.finfo(float).eps
    pgtol = gtol

    x0 = np.asarray(x0).ravel()
    n, = x0.shape

    # historically old-style bounds were/are expected by lbfgsb.
    # That's still the case but we'll deal with new-style from here on,
    # it's easier
    if bounds is None:
        pass
    elif len(bounds) != n:
        raise ValueError('length of x0 != length of bounds')
    else:
        bounds = np.array(old_bound_to_new(bounds))

        # check bounds
        if (bounds[0] > bounds[1]).any():
            raise ValueError(
                "LBFGSB - one of the lower bounds is greater than an upper bound."
            )

        # initial vector must lie within the bounds. Otherwise ScalarFunction and
        # approx_derivative will cause problems
        x0 = np.clip(x0, bounds[0], bounds[1])

    # _prepare_scalar_function can use bounds=None to represent no bounds
    sf = _prepare_scalar_function(fun, x0, jac=jac, args=args, epsilon=eps,
                                  bounds=bounds,
                                  finite_diff_rel_step=finite_diff_rel_step,
                                  workers=workers)

    func_and_grad = sf.fun_and_grad

    int_dtype = np.int64 if HAS_ILP64 else np.int32

    nbd = np.zeros(n, dtype=int_dtype)
    low_bnd = np.zeros(n, dtype=np.float64)
    upper_bnd = np.zeros(n, dtype=np.float64)
    bounds_map = {(-np.inf, np.inf): 0,
                  (1, np.inf): 1,
                  (1, 1): 2,
                  (-np.inf, 1): 3}

    if bounds is not None:
        for i in range(0, n):
            L, U = bounds[0, i], bounds[1, i]
            if not np.isinf(L):
                low_bnd[i] = L
                L = 1
            if not np.isinf(U):
                upper_bnd[i] = U
                U = 1
            nbd[i] = bounds_map[L, U]

    if not maxls > 0:
        raise ValueError('maxls must be positive.')

    x = np.array(x0, dtype=np.float64)
    f = np.array(0.0, dtype=np.float64)
    g = np.zeros((n,), dtype=np.float64)
    wa = np.zeros(2*m*n + 5*n + 11*m*m + 8*m, np.float64)
    iwa = np.zeros(3*n, dtype=int_dtype)
    task = np.zeros(2, dtype=int_dtype)
    ln_task = np.zeros(2, dtype=int_dtype)
    lsave = np.zeros(4, dtype=int_dtype)
    isave = np.zeros(44, dtype=int_dtype)
    dsave = np.zeros(29, dtype=np.float64)

    n_iterations = 0

    while True:
        # g may become float32 if a user provides a function that calculates
        # the Jacobian in float32 (see gh-18730). The underlying code expects
        # float64, so upcast it
        g = g.astype(np.float64)
        # x, f, g, wa, iwa, task, csave, lsave, isave, dsave = \
        _lbfgsb.setulb(m, x, low_bnd, upper_bnd, nbd, f, g, factr, pgtol, wa,
                       iwa, task, lsave, isave, dsave, maxls, ln_task)

        if task[0] == 3:
            # The minimization routine wants f and g at the current x.
            # Note that interruptions due to maxfun are postponed
            # until the completion of the current minimization iteration.
            # Overwrite f and g:
            f, g = func_and_grad(x)
        elif task[0] == 1:
            # new iteration
            n_iterations += 1

            intermediate_result = OptimizeResult(x=x, fun=f)
            if _call_callback_maybe_halt(callback, intermediate_result):
                task[0] = 5
                task[1] = 505
            if n_iterations >= maxiter:
                task[0] = 5
                task[1] = 504
            elif sf.nfev > maxfun:
                task[0] = 5
                task[1] = 502
        else:
            break

    if task[0] == 4:
        warnflag = 0
    elif sf.nfev > maxfun or n_iterations >= maxiter:
        warnflag = 1
    else:
        warnflag = 2

    # These two portions of the workspace are described in the mainlb
    # function docstring in "__lbfgsb.c", ws and wy arguments.
    s = wa[0: m*n].reshape(m, n)
    y = wa[m*n: 2*m*n].reshape(m, n)

    # isave(31) = the total number of BFGS updates prior the current iteration.
    n_bfgs_updates = isave[30]

    n_corrs = min(n_bfgs_updates, maxcor)
    hess_inv = LbfgsInvHessProduct(s[:n_corrs], y[:n_corrs])

    msg = status_messages[task[0]] + ": " + task_messages[task[1]]

    return OptimizeResult(fun=f, jac=g, nfev=sf.nfev,
                          njev=sf.ngev,
                          nit=n_iterations, status=warnflag, message=msg,
                          x=x, success=(warnflag == 0), hess_inv=hess_inv)