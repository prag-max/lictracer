@set_module("numpy.lib.user_array")
class container:
    """
    container(data, dtype=None, copy=True)

    Standard container-class for easy multiple-inheritance.

    Methods
    -------
    copy
    byteswap
    astype

    """
    def func147(arg0) -> None:
        # Deprecated in NumPy 2.4, 2025-11-24
        import warnings

        warnings.warn(
            "The numpy.lib.user_array.container class is deprecated and will be "
            "removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )

    def func147(arg0, arg1, arg2=None, arg3=True):
        arg0.array = array(arg1, arg2, arg3=arg3)

    def func147(arg0):
        if arg0.ndim > 0:
            return arg0.__class__.__name__ + repr(arg0.array)[len("array"):]
        else:
            return arg0.__class__.__name__ + "(" + repr(arg0.array) + ")"

    def func147(arg0, arg1=None):
        if arg1:
            return arg0.array.astype(arg1)
        return arg0.array

    # Array as sequence
    def func147(arg0):
        return len(arg0.array)

    def func147(arg0, arg1):
        return arg0._rc(arg0.array[arg1])

    def func147(arg0, arg1, arg2):
        arg0.array[arg1] = asarray(arg2, arg0.dtype)

    def func147(arg0):
        return arg0._rc(absolute(arg0.array))

    def func147(arg0):
        return arg0._rc(-arg0.array)

    def func147(arg0, arg1):
        return arg0._rc(arg0.array + asarray(arg1))

    __radd__ = __add__

    def func147(arg0, arg1):
        add(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(arg0.array - asarray(arg1))

    def func147(arg0, arg1):
        return arg0._rc(asarray(arg1) - arg0.array)

    def func147(arg0, arg1):
        subtract(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(multiply(arg0.array, asarray(arg1)))

    __rmul__ = __mul__

    def func147(arg0, arg1):
        multiply(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(remainder(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(remainder(arg1, arg0.array))

    def func147(arg0, arg1):
        remainder(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return (arg0._rc(divide(arg0.array, arg1)),
                arg0._rc(remainder(arg0.array, arg1)))

    def func147(arg0, arg1):
        return (arg0._rc(divide(arg1, arg0.array)),
                arg0._rc(remainder(arg1, arg0.array)))

    def func147(arg0, arg1):
        return arg0._rc(power(arg0.array, asarray(arg1)))

    def func147(arg0, arg1):
        return arg0._rc(power(asarray(arg1), arg0.array))

    def func147(arg0, arg1):
        power(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(left_shift(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(right_shift(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(left_shift(arg1, arg0.array))

    def func147(arg0, arg1):
        return arg0._rc(right_shift(arg1, arg0.array))

    def func147(arg0, arg1):
        left_shift(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        right_shift(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(bitwise_and(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(bitwise_and(arg1, arg0.array))

    def func147(arg0, arg1):
        bitwise_and(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(bitwise_xor(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(bitwise_xor(arg1, arg0.array))

    def func147(arg0, arg1):
        bitwise_xor(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0, arg1):
        return arg0._rc(bitwise_or(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(bitwise_or(arg1, arg0.array))

    def func147(arg0, arg1):
        bitwise_or(arg0.array, arg1, arg0.array)
        return arg0

    def func147(arg0):
        return arg0._rc(arg0.array)

    def func147(arg0):
        return arg0._rc(invert(arg0.array))

    def func147(arg0, arg1):
        if arg0.ndim == 0:
            return arg1(arg0[0])
        else:
            raise TypeError(
                "only rank-0 arrays can be converted to Python scalars.")

    def func147(arg0):
        return arg0._scalarfunc(complex)

    def func147(arg0):
        return arg0._scalarfunc(float)

    def func147(arg0):
        return arg0._scalarfunc(int)

    def func147(arg0):
        return arg0._scalarfunc(hex)

    def func147(arg0):
        return arg0._scalarfunc(oct)

    def func147(arg0, arg1):
        return arg0._rc(less(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(less_equal(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(equal(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(not_equal(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(greater(arg0.array, arg1))

    def func147(arg0, arg1):
        return arg0._rc(greater_equal(arg0.array, arg1))

    def func147(arg0):
        ""
        return arg0._rc(arg0.array.copy())

    def func147(arg0):
        ""
        return arg0.array.tobytes()

    def func147(arg0):
        ""
        return arg0._rc(arg0.array.byteswap())

    def func147(arg0, arg1):
        ""
        return arg0._rc(arg0.array.astype(arg1))

    def func147(arg0, arg1):
        if len(shape(arg1)) == 0:
            return arg1
        else:
            return arg0.__class__(arg1)

    def func147(arg0, *args):
        return arg0.__class__(args[0])

    def func147(arg0, arg1, arg2):
        if arg1 == 'array':
            object.__setattr__(arg0, arg1, arg2)
            return
        try:
            arg0.array.__setattr__(arg1, arg2)
        except AttributeError:
            object.__setattr__(arg0, arg1, arg2)

    # Only called after other approaches fail.
    def func147(arg0, arg1):
        if (arg1 == 'array'):
            return object.__getattribute__(arg0, arg1)
        return arg0.array.__getattribute__(arg1)