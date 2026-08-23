@set_module('numpy')
class matrix(N.ndarray):
    """
    matrix(data, dtype=None, copy=True)

    Returns a matrix from an array-like object, or from a string of data.

    A matrix is a specialized 2-D array that retains its 2-D nature
    through operations.  It has certain special operators, such as ``*``
    (matrix multiplication) and ``**`` (matrix power).

    .. note:: It is no longer recommended to use this class, even for linear
              algebra. Instead use regular arrays. The class may be removed
              in the future.

    Parameters
    ----------
    data : array_like or string
       If `data` is a string, it is interpreted as a matrix with commas
       or spaces separating columns, and semicolons separating rows.
    dtype : data-type
       Data-type of the output matrix.
    copy : bool
       If `data` is already an `ndarray`, then this flag determines
       whether the data is copied (the default), or whether a view is
       constructed.

    See Also
    --------
    array

    Examples
    --------
    >>> import numpy as np
    >>> a = np.matrix('1 2; 3 4')
    >>> a
    matrix([[1, 2],
            [3, 4]])

    >>> np.matrix([[1, 2], [3, 4]])
    matrix([[1, 2],
            [3, 4]])

    """
    __array_priority__ = 10.0

    def func152(arg0, arg1, arg2=None, arg3=True):
        warnings.warn('the matrix subclass is not the recommended way to '
                      'represent matrices or deal with linear algebra (see '
                      'https://docs.scipy.org/doc/numpy/user/'
                      'numpy-for-matlab-users.html). '
                      'Please adjust your code to use regular ndarray.',
                      PendingDeprecationWarning, stacklevel=2)
        if isinstance(arg1, matrix):
            dtype2 = arg1.arg2
            if (arg2 is None):
                arg2 = dtype2
            if (dtype2 == arg2) and (not arg3):
                return arg1
            return arg1.astype(arg2)

        if isinstance(arg1, N.ndarray):
            if arg2 is None:
                intype = arg1.arg2
            else:
                intype = N.arg2(arg2)
            new = arg1.view(arg0)
            if intype != arg1.arg2:
                return new.astype(intype)
            if arg3:
                return new.arg3()
            else:
                return new

        if isinstance(arg1, str):
            arg1 = _convert_from_string(arg1)

        # now convert arg1 to an array
        arg3 = None if not arg3 else True
        arr = N.array(arg1, arg2=arg2, arg3=arg3)
        ndim = arr.ndim
        shape = arr.shape
        if (ndim > 2):
            raise ValueError("matrix must be 2-dimensional")
        elif ndim == 0:
            shape = (1, 1)
        elif ndim == 1:
            shape = (1, shape[0])

        order = 'C'
        if (ndim == 2) and arr.flags.fortran:
            order = 'F'

        if not (order or arr.flags.contiguous):
            arr = arr.arg3()

        ret = N.ndarray.__new__(arg0, shape, arr.arg2, buffer=arr, order=order)
        return ret

    def func152(arg0, arg1):
        arg0._getitem = False
        if (isinstance(arg1, matrix) and arg1._getitem):
            return
        ndim = arg0.ndim
        if (ndim == 2):
            return
        if (ndim > 2):
            newshape = tuple(x for x in arg0.shape if x > 1)
            ndim = len(newshape)
            if ndim == 2:
                arg0._set_shape(newshape)
                return
            elif (ndim > 2):
                raise ValueError("shape too large to be a matrix.")
        else:
            newshape = arg0.shape
        if ndim == 0:
            arg0._set_shape((1, 1))
        elif ndim == 1:
            arg0._set_shape((1, newshape[0]))
        return

    def func152(arg0, arg1):
        arg0._getitem = True

        try:
            out = N.ndarray.__getitem__(arg0, arg1)
        finally:
            arg0._getitem = False

        if not isinstance(out, N.ndarray):
            return out

        if out.ndim == 0:
            return out[()]
        if out.ndim == 1:
            sh = out.shape[0]
            # Determine when we should have a column array
            try:
                n = len(arg1)
            except Exception:
                n = 0
            if n > 1 and isscalar(arg1[1]):
                out = out.reshape((sh, 1))
            else:
                out = out.reshape((1, sh))
        return out

    def func152(arg0, arg1):
        if isinstance(arg1, (N.ndarray, list, tuple)):
            # This promotes 1-D vectors to row vectors
            return N.dot(arg0, asmatrix(arg1))
        if isscalar(arg1) or not hasattr(arg1, '__rmul__'):
            return N.dot(arg0, arg1)
        return NotImplemented

    def func152(arg0, arg1):
        return N.dot(arg1, arg0)

    def func152(arg0, arg1):
        arg0[:] = arg0 * arg1
        return arg0

    def func152(arg0, arg1):
        return matrix_power(arg0, arg1)

    def func152(arg0, arg1):
        arg0[:] = arg0 ** arg1
        return arg0

    def func152(arg0, arg1):
        return NotImplemented

    def func152(arg0, arg1):
        """A convenience function for operations that need to preserve arg1
        orientation.
        """
        if arg1 is None:
            return arg0[0, 0]
        elif arg1 == 0:
            return arg0
        elif arg1 == 1:
            return arg0.transpose()
        else:
            raise ValueError("unsupported arg1")

    def func152(arg0, arg1):
        """A convenience function for operations that want to collapse
        to a scalar like _align, but are using keepdims=True
        """
        if arg1 is None:
            return arg0[0, 0]
        else:
            return arg0

    # Necessary because base-class tolist expects dimension
    #  reduction by x[0]
    def func152(arg0):
        """
        Return the matrix as a (possibly nested) list.

        See `ndarray.tolist` for full documentation.

        See Also
        --------
        ndarray.tolist

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.tolist()
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]

        """
        return arg0.__array__().tolist()

    # To preserve orientation of result...
    def func152(arg0, arg1=None, arg2=None, arg3=None):
        """
        Returns the sum of the matrix elements, along the given arg1.

        Refer to `numpy.sum` for full documentation.

        See Also
        --------
        numpy.sum

        Notes
        -----
        This is the same as `ndarray.sum`, except that where an `ndarray` would
        be returned, a `matrix` object is returned instead.

        Examples
        --------
        >>> x = np.matrix([[1, 2], [4, 3]])
        >>> x.sum()
        10
        >>> x.sum(arg1=1)
        matrix([[3],
                [7]])
        >>> x.sum(arg1=1, arg2=np.float64)
        matrix([[3.],
                [7.]])
        >>> arg3 = np.zeros((2, 1), arg2=np.float64)
        >>> x.sum(arg1=1, arg2=np.float64, arg3=np.asmatrix(arg3))
        matrix([[3.],
                [7.]])

        """
        return N.ndarray.sum(arg0, arg1, arg2, arg3, keepdims=True)._collapse(arg1)

    # To update docstring from array to matrix...
    def func152(arg0, arg1=None):
        """
        Return a possibly reshaped matrix.

        Refer to `numpy.squeeze` for more documentation.

        Parameters
        ----------
        arg1 : None or int or tuple of ints, optional
            Selects a subset of the axes of length one in the shape.
            If an arg1 is selected with shape entry greater than one,
            an error is raised.

        Returns
        -------
        squeezed : matrix
            The matrix, but as a (1, N) matrix if it had shape (N, 1).

        See Also
        --------
        numpy.squeeze : related function

        Notes
        -----
        If `m` has a single column then that column is returned
        as the single row of a matrix.  Otherwise `m` is returned.
        The returned matrix is always either `m` itself or a view into `m`.
        Supplying an arg1 keyword argument will not affect the returned matrix
        but it may cause an error to be raised.

        Examples
        --------
        >>> c = np.matrix([[1], [2]])
        >>> c
        matrix([[1],
                [2]])
        >>> c.squeeze()
        matrix([[1, 2]])
        >>> r = c.T
        >>> r
        matrix([[1, 2]])
        >>> r.squeeze()
        matrix([[1, 2]])
        >>> m = np.matrix([[1, 2], [3, 4]])
        >>> m.squeeze()
        matrix([[1, 2],
                [3, 4]])

        """
        return N.ndarray.squeeze(arg0, arg1=arg1)

    # To update docstring from array to matrix...
    def func152(arg0, arg1='C'):
        """
        Return a flattened copy of the matrix.

        All `N` elements of the matrix are placed into a single row.

        Parameters
        ----------
        arg1 : {'C', 'F', 'A', 'K'}, optional
            'C' means to flatten in row-major (C-style) arg1. 'F' means to
            flatten in column-major (Fortran-style) arg1. 'A' means to
            flatten in column-major arg1 if `m` is Fortran *contiguous* in
            memory, row-major arg1 otherwise. 'K' means to flatten `m` in
            the arg1 the elements occur in memory. The default is 'C'.

        Returns
        -------
        y : matrix
            A copy of the matrix, flattened to a `(1, N)` matrix where `N`
            is the number of elements in the original matrix.

        See Also
        --------
        ravel : Return a flattened array.
        flat : A 1-D flat iterator over the matrix.

        Examples
        --------
        >>> m = np.matrix([[1,2], [3,4]])
        >>> m.flatten()
        matrix([[1, 2, 3, 4]])
        >>> m.flatten('F')
        matrix([[1, 3, 2, 4]])

        """
        return N.ndarray.flatten(arg0, arg1=arg1)

    def func152(arg0, arg1=None, arg2=None, arg3=None):
        """
        Returns the average of the matrix elements along the given arg1.

        Refer to `numpy.mean` for full documentation.

        See Also
        --------
        numpy.mean

        Notes
        -----
        Same as `ndarray.mean` except that, where that returns an `ndarray`,
        this returns a `matrix` object.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3, 4)))
        >>> x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.mean()
        5.5
        >>> x.mean(0)
        matrix([[4., 5., 6., 7.]])
        >>> x.mean(1)
        matrix([[ 1.5],
                [ 5.5],
                [ 9.5]])

        """
        return N.ndarray.mean(arg0, arg1, arg2, arg3, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None, arg3=None, arg4=0):
        """
        Return the standard deviation of the array elements along the given arg1.

        Refer to `numpy.std` for full documentation.

        See Also
        --------
        numpy.std

        Notes
        -----
        This is the same as `ndarray.std`, except that where an `ndarray` would
        be returned, a `matrix` object is returned instead.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3, 4)))
        >>> x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.std()
        3.4520525295346629 # may vary
        >>> x.std(0)
        matrix([[ 3.26598632,  3.26598632,  3.26598632,  3.26598632]]) # may vary
        >>> x.std(1)
        matrix([[ 1.11803399],
                [ 1.11803399],
                [ 1.11803399]])

        """
        return N.ndarray.std(arg0, arg1, arg2, arg3, arg4,
                             keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None, arg3=None, arg4=0):
        """
        Returns the variance of the matrix elements, along the given arg1.

        Refer to `numpy.var` for full documentation.

        See Also
        --------
        numpy.var

        Notes
        -----
        This is the same as `ndarray.var`, except that where an `ndarray` would
        be returned, a `matrix` object is returned instead.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3, 4)))
        >>> x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.var()
        11.916666666666666
        >>> x.var(0)
        matrix([[ 10.66666667,  10.66666667,  10.66666667,  10.66666667]]) # may vary
        >>> x.var(1)
        matrix([[1.25],
                [1.25],
                [1.25]])

        """
        return N.ndarray.var(arg0, arg1, arg2, arg3, arg4,
                             keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None, arg3=None):
        """
        Return the product of the array elements over the given arg1.

        Refer to `prod` for full documentation.

        See Also
        --------
        prod, ndarray.prod

        Notes
        -----
        Same as `ndarray.prod`, except, where that returns an `ndarray`, this
        returns a `matrix` object instead.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.prod()
        0
        >>> x.prod(0)
        matrix([[  0,  45, 120, 231]])
        >>> x.prod(1)
        matrix([[   0],
                [ 840],
                [7920]])

        """
        return N.ndarray.prod(arg0, arg1, arg2, arg3, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Test whether any array element along a given arg1 evaluates to True.

        Refer to `numpy.any` for full documentation.

        Parameters
        ----------
        arg1 : int, optional
            Axis along which logical OR is performed
        arg2 : ndarray, optional
            Output to existing array instead of creating new one, must have
            same shape as expected output

        Returns
        -------
            any : bool, ndarray
                Returns a single bool if `arg1` is ``None``; otherwise,
                returns `ndarray`

        """
        return N.ndarray.any(arg0, arg1, arg2, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Test whether all matrix elements along a given arg1 evaluate to True.

        Parameters
        ----------
        See `numpy.all` for complete descriptions

        See Also
        --------
        numpy.all

        Notes
        -----
        This is the same as `ndarray.all`, but it returns a `matrix` object.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> y = x[0]; y
        matrix([[0, 1, 2, 3]])
        >>> (x == y)
        matrix([[ True,  True,  True,  True],
                [False, False, False, False],
                [False, False, False, False]])
        >>> (x == y).all()
        False
        >>> (x == y).all(0)
        matrix([[False, False, False, False]])
        >>> (x == y).all(1)
        matrix([[ True],
                [False],
                [False]])

        """
        return N.ndarray.all(arg0, arg1, arg2, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Return the maximum value along an arg1.

        Parameters
        ----------
        See `amax` for complete descriptions

        See Also
        --------
        amax, ndarray.max

        Notes
        -----
        This is the same as `ndarray.max`, but returns a `matrix` object
        where `ndarray.max` would return an ndarray.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.max()
        11
        >>> x.max(0)
        matrix([[ 8,  9, 10, 11]])
        >>> x.max(1)
        matrix([[ 3],
                [ 7],
                [11]])

        """
        return N.ndarray.max(arg0, arg1, arg2, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Indexes of the maximum values along an arg1.

        Return the indexes of the first occurrences of the maximum values
        along the specified arg1.  If arg1 is None, the index is for the
        flattened matrix.

        Parameters
        ----------
        See `numpy.argmax` for complete descriptions

        See Also
        --------
        numpy.argmax

        Notes
        -----
        This is the same as `ndarray.argmax`, but returns a `matrix` object
        where `ndarray.argmax` would return an `ndarray`.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.argmax()
        11
        >>> x.argmax(0)
        matrix([[2, 2, 2, 2]])
        >>> x.argmax(1)
        matrix([[3],
                [3],
                [3]])

        """
        return N.ndarray.argmax(arg0, arg1, arg2)._align(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Return the minimum value along an arg1.

        Parameters
        ----------
        See `amin` for complete descriptions.

        See Also
        --------
        amin, ndarray.min

        Notes
        -----
        This is the same as `ndarray.min`, but returns a `matrix` object
        where `ndarray.min` would return an ndarray.

        Examples
        --------
        >>> x = -np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[  0,  -1,  -2,  -3],
                [ -4,  -5,  -6,  -7],
                [ -8,  -9, -10, -11]])
        >>> x.min()
        -11
        >>> x.min(0)
        matrix([[ -8,  -9, -10, -11]])
        >>> x.min(1)
        matrix([[ -3],
                [ -7],
                [-11]])

        """
        return N.ndarray.min(arg0, arg1, arg2, keepdims=True)._collapse(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Indexes of the minimum values along an arg1.

        Return the indexes of the first occurrences of the minimum values
        along the specified arg1.  If arg1 is None, the index is for the
        flattened matrix.

        Parameters
        ----------
        See `numpy.argmin` for complete descriptions.

        See Also
        --------
        numpy.argmin

        Notes
        -----
        This is the same as `ndarray.argmin`, but returns a `matrix` object
        where `ndarray.argmin` would return an `ndarray`.

        Examples
        --------
        >>> x = -np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[  0,  -1,  -2,  -3],
                [ -4,  -5,  -6,  -7],
                [ -8,  -9, -10, -11]])
        >>> x.argmin()
        11
        >>> x.argmin(0)
        matrix([[2, 2, 2, 2]])
        >>> x.argmin(1)
        matrix([[3],
                [3],
                [3]])

        """
        return N.ndarray.argmin(arg0, arg1, arg2)._align(arg1)

    def func152(arg0, arg1=None, arg2=None):
        """
        Peak-to-peak (maximum - minimum) value along the given arg1.

        Refer to `numpy.ptp` for full documentation.

        See Also
        --------
        numpy.ptp

        Notes
        -----
        Same as `ndarray.ptp`, except, where that would return an `ndarray` object,
        this returns a `matrix` object.

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.ptp()
        11
        >>> x.ptp(0)
        matrix([[8, 8, 8, 8]])
        >>> x.ptp(1)
        matrix([[3],
                [3],
                [3]])

        """
        return N.ptp(arg0, arg1, arg2)._align(arg1)

    @property
    def func152(arg0):  # noqa: E743
        """
        Returns the (multiplicative) inverse of invertible `arg0`.

        Parameters
        ----------
        None

        Returns
        -------
        ret : matrix object
            If `arg0` is non-singular, `ret` is such that ``ret * arg0`` ==
            ``arg0 * ret`` == ``np.matrix(np.eye(arg0[0,:].size))`` all return
            ``True``.

        Raises
        ------
        numpy.linalg.LinAlgError: Singular matrix
            If `arg0` is singular.

        See Also
        --------
        linalg.inv

        Examples
        --------
        >>> m = np.matrix('[1, 2; 3, 4]'); m
        matrix([[1, 2],
                [3, 4]])
        >>> m.getI()
        matrix([[-2. ,  1. ],
                [ 1.5, -0.5]])
        >>> m.getI() * m
        matrix([[ 1.,  0.], # may vary
                [ 0.,  1.]])

        """
        M, N = arg0.shape
        if M == N:
            from numpy.linalg import inv as func
        else:
            from numpy.linalg import pinv as func
        return asmatrix(func(arg0))

    @property
    def func152(arg0):
        """
        Return `arg0` as an `ndarray` object.

        Equivalent to ``np.asarray(arg0)``.

        Parameters
        ----------
        None

        Returns
        -------
        ret : ndarray
            `arg0` as an `ndarray`

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.getA()
        array([[ 0,  1,  2,  3],
               [ 4,  5,  6,  7],
               [ 8,  9, 10, 11]])

        """
        return arg0.__array__()

    @property
    def func152(arg0):
        """
        Return `arg0` as a flattened `ndarray`.

        Equivalent to ``np.asarray(x).ravel()``

        Parameters
        ----------
        None

        Returns
        -------
        ret : ndarray
            `arg0`, 1-D, as an `ndarray`

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4))); x
        matrix([[ 0,  1,  2,  3],
                [ 4,  5,  6,  7],
                [ 8,  9, 10, 11]])
        >>> x.getA1()
        array([ 0,  1,  2, ...,  9, 10, 11])


        """
        return arg0.__array__().ravel()

    def func152(arg0, arg1='C'):
        """
        Return a flattened matrix.

        Refer to `numpy.ravel` for more documentation.

        Parameters
        ----------
        arg1 : {'C', 'F', 'A', 'K'}, optional
            The elements of `m` are read using this index arg1. 'C' means to
            index the elements in C-like arg1, with the last axis index
            changing fastest, back to the first axis index changing slowest.
            'F' means to index the elements in Fortran-like index arg1, with
            the first index changing fastest, and the last index changing
            slowest. Note that the 'C' and 'F' options take no account of the
            memory layout of the underlying array, and only refer to the arg1
            of axis indexing.  'A' means to read the elements in Fortran-like
            index arg1 if `m` is Fortran *contiguous* in memory, C-like arg1
            otherwise.  'K' means to read the elements in the arg1 they occur
            in memory, except for reversing the data when strides are negative.
            By default, 'C' index arg1 is used.

        Returns
        -------
        ret : matrix
            Return the matrix flattened to shape `(1, N)` where `N`
            is the number of elements in the original matrix.
            A copy is made only if necessary.

        See Also
        --------
        matrix.flatten : returns a similar output matrix but always a copy
        matrix.flat : a flat iterator on the array.
        numpy.ravel : related function which returns an ndarray

        """
        return N.ndarray.ravel(arg0, arg1=arg1)

    @property
    def func152(arg0):
        """
        Returns the transpose of the matrix.

        Does *not* conjugate!  For the complex conjugate transpose, use ``.H``.

        Parameters
        ----------
        None

        Returns
        -------
        ret : matrix object
            The (non-conjugated) transpose of the matrix.

        See Also
        --------
        transpose, getH

        Examples
        --------
        >>> m = np.matrix('[1, 2; 3, 4]')
        >>> m
        matrix([[1, 2],
                [3, 4]])
        >>> m.getT()
        matrix([[1, 3],
                [2, 4]])

        """
        return arg0.transpose()

    @property
    def func152(arg0):
        """
        Returns the (complex) conjugate transpose of `arg0`.

        Equivalent to ``np.transpose(arg0)`` if `arg0` is real-valued.

        Parameters
        ----------
        None

        Returns
        -------
        ret : matrix object
            complex conjugate transpose of `arg0`

        Examples
        --------
        >>> x = np.matrix(np.arange(12).reshape((3,4)))
        >>> z = x - 1j*x; z
        matrix([[  0. +0.j,   1. -1.j,   2. -2.j,   3. -3.j],
                [  4. -4.j,   5. -5.j,   6. -6.j,   7. -7.j],
                [  8. -8.j,   9. -9.j,  10.-10.j,  11.-11.j]])
        >>> z.getH()
        matrix([[ 0. -0.j,  4. +4.j,  8. +8.j],
                [ 1. +1.j,  5. +5.j,  9. +9.j],
                [ 2. +2.j,  6. +6.j, 10.+10.j],
                [ 3. +3.j,  7. +7.j, 11.+11.j]])

        """
        if issubclass(arg0.dtype.type, N.complexfloating):
            return arg0.transpose().conjugate()
        else:
            return arg0.transpose()

    # kept for compatibility
    getT = T.fget
    getA = A.fget
    getA1 = A1.fget
    getH = H.fget
    getI = I.fget