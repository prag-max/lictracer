def customize_result(res, shape):
        n = res['x'].shape[0] // 2

        # To avoid ambiguity, below we refer to `xl0`, the initial left endpoint
        # as `a` and `xr0`, the initial right endpoint, as `b`.
        # Because we treat the two one-sided searches as though they were
        # independent, what we keep track of in `work` and what we want to
        # return in `res` look quite different. Combine the results from the
        # two one-sided searches before reporting the results to the user.
        # - "a" refers to the leftward search (the moving end started at `a`)
        # - "b" refers to the rightward search (the moving end started at `b`)
        # - "l" refers to the left end of the bracket (closer to -oo)
        # - "r" refers to the right end of the bracket (closer to +oo)
        xar = res['x_last'][:n]
        xbl = res['x_last'][n:]
        xbr = res['x'][n:]

        fal = res['f'][:n]
        far = res['f_last'][:n]
        fbl = res['f_last'][n:]
        fbr = res['f'][n:]

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
        sa = res['status'][:n]
        sb = res['status'][n:]

        da = xar - xal
        db = xbr - xbl

        i1 = ((da <= db) & (sa == 0)) | ((sa == 0) & (sb != 0))
        i2 = ((db <= da) & (sb == 0)) | ((sb == 0) & (sa != 0))

        xr[i1] = xar[i1]
        fr[i1] = far[i1]
        xl[i2] = xbl[i2]
        fl[i2] = fbl[i2]

        # Finish assembling the result object
        res['xl'] = xl
        res['xr'] = xr
        res['fl'] = fl
        res['fr'] = fr

        res['nit'] = xp.maximum(res['nit'][:n], res['nit'][n:])
        res['nfev'] = res['nfev'][:n] + res['nfev'][n:]
        # If the status on one side is zero, the status is zero. In any case,
        # report the status from one side only.
        res['status'] = xp.where(sa == 0, sa, sb)
        res['success'] = (res['status'] == 0)

        del res['x']
        del res['f']
        del res['x_last']
        del res['f_last']

        return shape[:-1]