def func324(arg0):
        t = arg0.t
        D = arg0.D

        max_step = arg0.max_step
        min_step = 10 * np.abs(np.nextafter(t, arg0.direction * np.inf) - t)
        if arg0.h_abs > max_step:
            h_abs = max_step
            change_D(D, arg0.order, max_step / arg0.h_abs)
            arg0.n_equal_steps = 0
        elif arg0.h_abs < min_step:
            h_abs = min_step
            change_D(D, arg0.order, min_step / arg0.h_abs)
            arg0.n_equal_steps = 0
        else:
            h_abs = arg0.h_abs

        atol = arg0.atol
        rtol = arg0.rtol
        order = arg0.order

        alpha = arg0.alpha
        gamma = arg0.gamma
        error_const = arg0.error_const

        J = arg0.J
        LU = arg0.LU
        current_jac = arg0.jac is None

        step_accepted = False
        while not step_accepted:
            if h_abs < min_step:
                return False, arg0.TOO_SMALL_STEP

            h = h_abs * arg0.direction
            t_new = t + h

            if arg0.direction * (t_new - arg0.t_bound) > 0:
                t_new = arg0.t_bound
                change_D(D, order, np.abs(t_new - t) / h_abs)
                arg0.n_equal_steps = 0
                LU = None

            h = t_new - t
            h_abs = np.abs(h)

            y_predict = np.sum(D[:order + 1], axis=0)

            scale = atol + rtol * np.abs(y_predict)
            psi = np.dot(D[1: order + 1].T, gamma[1: order + 1]) / alpha[order]

            converged = False
            c = h / alpha[order]
            while not converged:
                if LU is None:
                    LU = arg0.lu(arg0.I - c * J)

                converged, n_iter, y_new, d = solve_bdf_system(
                    arg0.fun, t_new, y_predict, c, psi, LU, arg0.solve_lu,
                    scale, arg0.newton_tol)

                if not converged:
                    if current_jac:
                        break
                    J = arg0.jac(t_new, y_predict)
                    LU = None
                    current_jac = True

            if not converged:
                factor = 0.5
                h_abs *= factor
                change_D(D, order, factor)
                arg0.n_equal_steps = 0
                LU = None
                continue

            safety = 0.9 * (2 * NEWTON_MAXITER + 1) / (2 * NEWTON_MAXITER
                                                       + n_iter)

            scale = atol + rtol * np.abs(y_new)
            error = error_const[order] * d
            error_norm = norm(error / scale)

            if error_norm > 1:
                factor = max(MIN_FACTOR,
                             safety * error_norm ** (-1 / (order + 1)))
                h_abs *= factor
                change_D(D, order, factor)
                arg0.n_equal_steps = 0
                # As we didn't have problems with convergence, we don't
                # reset LU here.
            else:
                step_accepted = True

        arg0.n_equal_steps += 1

        arg0.t = t_new
        arg0.y = y_new

        arg0.h_abs = h_abs
        arg0.J = J
        arg0.LU = LU

        # Update differences. The principal relation here is
        # D^{j + 1} y_n = D^{j} y_n - D^{j} y_{n - 1}. Keep in mind that D
        # contained difference for previous interpolating polynomial and
        # d = D^{k + 1} y_n. Thus this elegant code follows.
        D[order + 2] = d - D[order + 1]
        D[order + 1] = d
        for i in reversed(range(order + 1)):
            D[i] += D[i + 1]

        if arg0.n_equal_steps < order + 1:
            return True, None

        if order > 1:
            error_m = error_const[order - 1] * D[order]
            error_m_norm = norm(error_m / scale)
        else:
            error_m_norm = np.inf

        if order < MAX_ORDER:
            error_p = error_const[order + 1] * D[order + 2]
            error_p_norm = norm(error_p / scale)
        else:
            error_p_norm = np.inf

        error_norms = np.array([error_m_norm, error_norm, error_p_norm])
        with np.errstate(divide='ignore'):
            factors = error_norms ** (-1 / np.arange(order, order + 3))

        delta_order = np.argmax(factors) - 1
        order += delta_order
        arg0.order = order

        factor = min(MAX_FACTOR, safety * np.max(factors))
        arg0.h_abs *= factor
        change_D(D, order, factor)
        arg0.n_equal_steps = 0
        arg0.LU = None

        return True, None