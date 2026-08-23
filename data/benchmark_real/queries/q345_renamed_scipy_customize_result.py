def func344(arg0, arg1):
        n = arg0['x'].arg1[0] // 2

        # To avoid ambiguity, below we refer to `xl0`, the initial left endpoint
        # as `a` and `xr0`, the initial right endpoint, as `b`.
        # Because we treat the two one-sided searches as though they were
        # independent, what we keep track of in `work` and what we want to
        # return in `arg0` look quite different. Combine the results from the
        # two one-sided searches before reporting the results to the user.
        # - "a" refers to the leftward search (the moving end started at `a`)
        # - "b" refers to the rightward search (the moving end started at `b`)
        # - "l" refers to the left end of the bracket (closer to -oo)
        # - "r" refers to the right end of the bracket (closer to +oo)
        xal = arg0['x'][:n]
        xar = arg0['x_last'][:n]
        xbl = arg0['x_last'][n:]
        xbr = arg0['x'][n:]

        fal = arg0['f'][:n]
        far = arg0['f_last'][:n]
        fbl = arg0['f_last'][n:]
        fbr = arg0['f'][n:]

        # Initialize the brackets and corresponding function values to return
        # to the user. Brackets may not be valid (e.g. there is no root,
        # there weren't enough iterations, NaN encountered), but we still need
        # to return something. One option would be all NaNs, but what I've
        # chosen here is the left- and right-most points at which the function
        # has been evaluated. This gives the user some information about what
        # interval of the real line has been searched and shows that there is
        # no sign change between the two ends.
        xl = xp.asarray(xal, copy=True)
        fl = xp.asarray(fal, copy=True)
        xr = xp.asarray(xbr, copy=True)
        fr = xp.asarray(fbr, copy=True)

        # `status` indicates whether the bracket is valid or not. If so,
        # we want to adjust the bracket we return to be the narrowest possible
        # given the points at which we evaluated the function.
        # For example if bracket "a" is valid and smaller than bracket "b" OR
        # if bracket "a" is valid and bracket "b" is not valid, we want to
        # return bracket "a" (and vice versa).
        sa = arg0['status'][:n]
        sb = arg0['status'][n:]

        da = xar - xal
        db = xbr - xbl

        i1 = ((da <= db) & (sa == 0)) | ((sa == 0) & (sb != 0))
        i2 = ((db <= da) & (sb == 0)) | ((sb == 0) & (sa != 0))

        xr[i1] = xar[i1]
        fr[i1] = far[i1]
        xl[i2] = xbl[i2]
        fl[i2] = fbl[i2]

        # Finish assembling the result object
        arg0['xl'] = xl
        arg0['xr'] = xr
        arg0['fl'] = fl
        arg0['fr'] = fr

        arg0['nit'] = xp.maximum(arg0['nit'][:n], arg0['nit'][n:])
        arg0['nfev'] = arg0['nfev'][:n] + arg0['nfev'][n:]
        # If the status on one side is zero, the status is zero. In any case,
        # report the status from one side only.
        arg0['status'] = xp.where(sa == 0, sa, sb)
        arg0['success'] = (arg0['status'] == 0)

        del arg0['x']
        del arg0['f']
        del arg0['x_last']
        del arg0['f_last']

        return arg1[:-1]