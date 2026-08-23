def _bracket_minimum(func, xm0, *, xl0=None, xr0=None, xmin=None, xmax=None,
                     factor=None, args=(), kwargs=None, maxiter=1000):
    """Bracket the minimum of a unimodal scalar function of one variable

    This function works elementwise when `xm0`, `xl0`, `xr0`, `xmin`, `xmax`,
    and the elements of `args` are broadcastable arrays.

    Parameters
    ----------
    func : callable
        The function for which the minimum is to be bracketed.
        The signature must be::

            func(x: ndarray, *args) -> ndarray

        where each element of ``x`` is a finite real and ``args`` is a tuple,
        which may contain an arbitrary number of arrays that are broadcastable
        with ``x``. `func` must be an elementwise function: each element
        ``func(x)[i]`` must equal ``func(x[i])`` for all indices `i`.
    xm0: float array_like
        Starting guess for middle point of bracket.
    xl0, xr0: float array_like, optional
        Starting guesses for left and right endpoints of the bracket. Must be
        broadcastable with one another and with `xm0`.
    xmin, xmax : float array_like, optional
        Minimum and maximum allowable endpoints of the bracket, inclusive. Must
        be broadcastable with `xl0`, `xm0`, and `xr0`.
    factor : float array_like, optional
        Controls expansion of bracket endpoint in downhill direction. Works
        differently in the cases where a limit is set in the downhill direction
        with `xmax` or `xmin`. See Notes.
    args : tuple, optional
        Additional positional arguments to be passed to `func`.  Must be arrays
        broadcastable with `xl0`, `xm0`, `xr0`, `xmin`, and `xmax`. If the
        callable to be bracketed requires arguments that are not broadcastable
        with these arrays, wrap that callable with `func` such that `func`
        accepts only ``x`` and broadcastable arrays.
    kwargs : dict of str:array_like, optional
        Additional keyword arguments to be passed to `f`. See `args`.
    maxiter : int, optional
        The maximum number of iterations of the algorithm to perform. The number
        of function evaluations is three greater than the number of iterations.

    Returns
    -------
    res : _RichResult
        An instance of `scipy._lib._util._RichResult` with the following
        attributes. The descriptions are written as though the values will be
        scalars; however, if `func` returns an array, the outputs will be
        arrays of the same shape.

        xl, xm, xr : float
            The left, middle, and right points of the bracket, if the algorithm
            terminated successfully.
        fl, fm, fr : float
            The function value at the left, middle, and right points of the bracket.
        nfev : int
            The number of function evaluations required to find the bracket.
        nit : int
            The number of iterations of the algorithm that were performed.
        status : int
            An integer representing the exit status of the algorithm.

            - ``0`` : The algorithm produced a valid bracket.
            - ``-1`` : The bracket expanded to the allowable limits. Assuming
                       unimodality, this implies the endpoint at the limit is a
                       minimizer.
            - ``-2`` : The maximum number of iterations was reached.
            - ``-3`` : A non-finite value was encountered.
            - ``-4`` : ``None`` shall pass.
            - ``-5`` : The initial bracket does not satisfy
                       `xmin <= xl0 < xm0 < xr0 <= xmax`.

        success : bool
            ``True`` when the algorithm terminated successfully (status ``0``).

    Notes
    -----
    Similar to `scipy.optimize.bracket`, this function seeks to find real
    points ``xl < xm < xr`` such that ``f(xl) >= f(xm)`` and ``f(xr) >= f(xm)``,
    where at least one of the inequalities is strict. Unlike `scipy.optimize.bracket`,
    this function can operate in a vectorized manner on array input, so long as
    the input arrays are broadcastable with each other. Also unlike
    `scipy.optimize.bracket`, users may specify minimum and maximum endpoints
    for the desired bracket.

    Given an initial trio of points ``xl = xl0``, ``xm = xm0``, ``xr = xr0``,
    the algorithm checks if these points already give a valid bracket. If not,
    a new endpoint, ``w`` is chosen in the "downhill" direction, ``xm`` becomes the new
    opposite endpoint, and either `xl` or `xr` becomes the new middle point,
    depending on which direction is downhill. The algorithm repeats from here.

    The new endpoint `w` is chosen differently depending on whether or not a
    boundary `xmin` or `xmax` has been set in the downhill direction. Without
    loss of generality, suppose the downhill direction is to the right, so that
    ``f(xl) > f(xm) > f(xr)``. If there is no boundary to the right, then `w`
    is chosen to be ``xr + factor * (xr - xm)`` where `factor` is controlled by
    the user (defaults to 2.0) so that step sizes increase in geometric proportion.
    If there is a boundary, `xmax` in this case, then `w` is chosen to be
    ``xmax - (xmax - xr)/factor``, with steps slowing to a stop at
    `xmax`. This cautious approach ensures that a minimum near but distinct from
    the boundary isn't missed while also detecting whether or not the `xmax` is
    a minimizer when `xmax` is reached after a finite number of steps.
    """  # noqa: E501
    callback = None  # works; I just don't want to test it

    temp = _bracket_minimum_iv(func, xm0, xl0, xr0, xmin, xmax,
                               factor, args, kwargs, maxiter)
    func, xm0, xl0, xr0, xmin, xmax, factor, args, kwargs, maxiter, xp = temp

    xs = (xl0, xm0, xr0)
    temp = eim._initialize(func, xs, args, kwargs=kwargs)
    func, xs, fs, args, shape, dtype, xp = temp

    xl0, xm0, xr0 = xs
    fl0, fm0, fr0 = fs
    xmin = xp.astype(xp.broadcast_to(xmin, shape), dtype, copy=False)
    xmin = xp_ravel(xmin, xp=xp)
    xmax = xp.astype(xp.broadcast_to(xmax, shape), dtype, copy=False)
    xmax = xp_ravel(xmax, xp=xp)
    invalid_bracket = ~((xmin <= xl0) & (xl0 < xm0) & (xm0 < xr0) & (xr0 <= xmax))
    # We will modify factor later on so make a copy. np.broadcast_to returns
    # a read-only view.
    factor = xp.astype(xp.broadcast_to(factor, shape), dtype, copy=True)
    factor = xp_ravel(factor)

    # To simplify the logic, swap xl and xr if f(xl) < f(xr). We should always be
    # marching downhill in the direction from xl to xr.
    comp = fl0 < fr0
    xl0[comp], xr0[comp] = xr0[comp], xl0[comp]
    fl0[comp], fr0[comp] = fr0[comp], fl0[comp]
    # We only need the boundary in the direction we're traveling.
    limit = xp.where(comp, xmin, xmax)

    unlimited = xp.isinf(limit)
    limited = ~unlimited
    step = xp.empty_like(xl0)

    step[unlimited] = (xr0[unlimited] - xm0[unlimited])
    step[limited] = (limit[limited] - xr0[limited])

    # Step size is divided by factor for case where there is a limit.
    factor[limited] = 1 / factor[limited]

    status = xp.full_like(xl0, eim._EINPROGRESS, dtype=xp.int32)
    status[invalid_bracket] = eim._EINPUTERR
    nit, nfev = 0, 3

    work = _RichResult(xl=xl0, xm=xm0, xr=xr0, xr0=xr0, fl=fl0, fm=fm0, fr=fr0,
                       step=step, limit=limit, limited=limited, factor=factor, nit=nit,
                       nfev=nfev, status=status, args=args)

    res_work_pairs = [('status', 'status'), ('xl', 'xl'), ('xm', 'xm'), ('xr', 'xr'),
                      ('nit', 'nit'), ('nfev', 'nfev'), ('fl', 'fl'), ('fm', 'fm'),
                      ('fr', 'fr')]

    def func329(arg0):
        arg0.step *= arg0.factor
        x = xp.empty_like(arg0.xr)
        x[~arg0.limited] = arg0.xr0[~arg0.limited] + arg0.step[~arg0.limited]
        x[arg0.limited] = arg0.limit[arg0.limited] - arg0.step[arg0.limited]
        # Since the new bracket endpoint is calculated from an offset with the
        # limit, it may be the case that the new endpoint equals the old endpoint,
        # when the old endpoint is sufficiently close to the limit. We use the
        # limit itself as the new endpoint in these cases.
        x[arg0.limited] = xp.where(
            x[arg0.limited] == arg0.xr[arg0.limited],
            arg0.limit[arg0.limited],
            x[arg0.limited],
        )
        return x

    def func329(arg0, arg1, arg2):
        arg2.xl, arg2.xm, arg2.xr = arg2.xm, arg2.xr, arg0
        arg2.fl, arg2.fm, arg2.fr = arg2.fm, arg2.fr, arg1

    def func329(arg0):
        # Condition 0: Initial bracket is invalid.
        stop = (arg0.status == eim._EINPUTERR)

        # Condition 1: A valid bracket has been found.
        i = (
            (arg0.fl >= arg0.fm) & (arg0.fr > arg0.fm)
            | (arg0.fl > arg0.fm) & (arg0.fr >= arg0.fm)
        ) & ~stop
        arg0.status[i] = eim._ECONVERGED
        stop[i] = True

        # Condition 2: Moving end of bracket reaches limit.
        i = (arg0.xr == arg0.limit) & ~stop
        arg0.status[i] = _ELIMITS
        stop[i] = True

        # Condition 3: non-finite value encountered
        i = ~(xp.isfinite(arg0.xr) & xp.isfinite(arg0.fr)) & ~stop
        arg0.status[i] = eim._EVALUEERR
        stop[i] = True

        return stop

    def func329(arg0):
        pass

    def func329(arg0, arg1):
        # Reorder entries of xl and xr if they were swapped due to f(xl0) < f(xr0).
        comp = arg0['xl'] > arg0['xr']
        arg0['xl'][comp], arg0['xr'][comp] = arg0['xr'][comp], arg0['xl'][comp]
        arg0['fl'][comp], arg0['fr'][comp] = arg0['fr'][comp], arg0['fl'][comp]
        return arg1

    return eim._loop(work, callback, arg1,
                     maxiter, func, args, dtype,
                     pre_func_eval, post_func_eval,
                     check_termination, post_termination_check,
                     customize_result, res_work_pairs, xp)