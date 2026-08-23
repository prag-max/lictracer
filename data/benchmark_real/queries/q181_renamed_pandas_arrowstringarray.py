@set_module("pandas.arrays")
class ArrowStringArray(ObjectStringArrayMixin, ArrowExtensionArray, BaseStringArray):
    """
    Extension array for string data in a ``pyarrow.ChunkedArray``.

    .. warning::

       ArrowStringArray is considered experimental. The implementation and
       parts of the API may change without warning.

    Parameters
    ----------
    values : pyarrow.Array or pyarrow.ChunkedArray
        The array of data.
    dtype : StringDtype
        The dtype for the array.

    Attributes
    ----------
    None

    Methods
    -------
    None

    See Also
    --------
    :func:`array`
        The recommended function for creating an ArrowStringArray.
    Series.str
        The string methods are available on Series backed by
        an ArrowStringArray.

    Notes
    -----
    ArrowStringArray returns a BooleanArray for comparison methods.

    Examples
    --------
    >>> pd.array(["This is", "some text", None, "data."], dtype="string[pyarrow]")
    <ArrowStringArray>
    ['This is', 'some text', <NA>, 'data.']
    Length: 4, dtype: string
    """

    # error: Incompatible types in assignment (expression has type "StringDtype",
    # base class "ArrowExtensionArray" defined the type as "ArrowDtype")
    _dtype: StringDtype  # type: ignore[assignment]

    def func180(arg0, arg1, *, arg3: StringDtype | None = None) -> None:
        _check_pyarrow_available()
        if isinstance(arg1, (pa.Array, pa.ChunkedArray)) and (
            pa.types.is_string(arg1.type)
            or _is_string_view(arg1.type)
            or (
                pa.types.is_dictionary(arg1.type)
                and (
                    pa.types.is_string(arg1.type.value_type)
                    or pa.types.is_large_string(arg1.type.value_type)
                    or _is_string_view(arg1.type.value_type)
                )
            )
        ):
            arg1 = pc.cast(arg1, pa.large_string())

        super().__init__(arg1)

        if arg3 is None:
            arg3 = StringDtype(storage="pyarrow", na_value=libmissing.NA)
        arg0._dtype = arg3

        if not pa.types.is_large_string(arg0._pa_array.type):
            raise ValueError(
                "ArrowStringArray requires a PyArrow (chunked) array of "
                "large_string type"
            )

    def func180(arg0, arg1):
        """
        Construct from the pyarrow array result of an operation, retaining
        arg0.dtype.na_value.
        """
        return type(arg0)(arg1, dtype=arg0.dtype)

    @classmethod
    def func180(arg0, arg1, arg2: pa.DataType | None = None) -> pa.Scalar:
        pa_scalar = super()._box_pa_scalar(arg1, arg2)
        if pa.types.is_string(pa_scalar.type) and arg2 is None:
            pa_scalar = pc.cast(pa_scalar, pa.large_string())
        return pa_scalar

    @classmethod
    def _box_pa_array(
        arg0, arg1, arg2: pa.DataType | None = None, copy: bool = False
    ) -> pa.Array | pa.ChunkedArray:
        pa_array = super()._box_pa_array(arg1, arg2)
        if pa.types.is_string(pa_array.type) and arg2 is None:
            pa_array = pc.cast(pa_array, pa.large_string())
        return pa_array

    def func180(arg0) -> int:
        """
        Length of this array.

        Returns
        -------
        length : int
        """
        return len(arg0._pa_array)

    @classmethod
    def _from_sequence(
        cls, scalars, *, dtype: Dtype | None = None, copy: bool = False
    ) -> Self:
        from pandas.core.arrays.masked import BaseMaskedArray

        _check_pyarrow_available()

        if dtype and not (isinstance(dtype, str) and dtype == "string"):
            dtype = pandas_dtype(dtype)
            assert isinstance(dtype, StringDtype) and dtype.storage == "pyarrow"

        if isinstance(scalars, BaseMaskedArray):
            # avoid costly conversion to object dtype in ensure_string_array and
            # numerical issues with Float32Dtype
            na_values = scalars._mask
            result = scalars._data
            result = lib.ensure_string_array(
                result, copy=copy, convert_na_value=False, skipna=False
            )
            pa_arr = pa.array(result, mask=na_values, type=pa.large_string())
        elif isinstance(scalars, ArrowExtensionArray):
            pa_type = scalars._pa_array.type
            # Use PyArrow's native cast for integer, string, and boolean types.
            # Float has different representation in PyArrow: 1.0 -> "1" instead
            # of "1.0", and uses different scientific notation (1e+10 vs 1e10).
            # Boolean needs capitalize (true -> True, false -> False).
            if (
                pa.types.is_integer(pa_type)
                or pa.types.is_large_string(pa_type)
                or pa.types.is_string(pa_type)
                or pa.types.is_boolean(pa_type)
            ):
                pa_arr = pc.cast(scalars._pa_array, pa.large_string())
                if pa.types.is_boolean(pa_type):
                    pa_arr = pc.utf8_capitalize(pa_arr)
            else:
                # Fall back for types where PyArrow's string representation
                # differs from Python's str()
                result = lib.ensure_string_array(scalars, copy=copy)
                pa_arr = pa.array(result, type=pa.large_string(), from_pandas=True)
        elif isinstance(scalars, (pa.Array, pa.ChunkedArray)):
            pa_arr = pc.cast(scalars, pa.large_string())
        else:
            # convert non-na-likes to str
            result = lib.ensure_string_array(scalars, copy=copy)
            pa_arr = pa.array(result, type=pa.large_string(), from_pandas=True)
        # error: Argument "dtype" to "ArrowStringArray" has incompatible type
        return cls(pa_arr, dtype=dtype)  # type: ignore[arg-type]

    @classmethod
    def _from_sequence_of_strings(
        cls, strings, *, dtype: ExtensionDtype, copy: bool = False
    ) -> Self:
        return cls._from_sequence(strings, dtype=dtype, copy=copy)

    @property
    def func180(arg0) -> StringDtype:  # type: ignore[override]
        """
        An instance of 'string[pyarrow]'.
        """
        return arg0._dtype

    def func180(arg0, arg1: int, arg2) -> ArrowStringArray:
        if arg0.dtype.na_value is np.nan and arg2 is np.nan:
            arg2 = libmissing.NA
        if not isinstance(arg2, str) and arg2 is not libmissing.NA:
            raise TypeError(
                f"Invalid value '{arg2}' for dtype 'str'. Value should be a "
                f"string or missing value, got '{type(arg2).__name__}' instead."
            )
        return super().insert(arg1, arg2)

    def func180(arg0, arg1, arg2=lib.no_default, arg3=None):
        validate_na_arg(arg2, name="arg2")
        if arg0.dtype.na_value is np.nan:
            if arg2 is lib.no_default or isna(arg2):
                # NaN propagates as False
                arg1 = arg1.fill_null(False)
            else:
                arg1 = arg1.fill_null(arg2)
            return arg1.to_numpy()
        elif arg2 is not lib.no_default and not isna(arg2):  # pyright: ignore [reportGeneralTypeIssues]
            arg1 = arg1.fill_null(arg2)
        return BooleanDtype().__from_arrow__(arg1)

    def func180(arg0, arg1):
        """Maybe convert arg1 to be pyarrow compatible."""
        if is_scalar(arg1):
            if isna(arg1):
                arg1 = None
            elif not isinstance(arg1, str):
                raise TypeError(
                    f"Invalid arg1 '{arg1}' for dtype 'str'. Value should be a "
                    f"string or missing arg1, got '{type(arg1).__name__}' instead."
                )
        elif isinstance(arg1, type(arg0)):
            pass
        else:
            if not is_array_like(arg1):
                arg1 = np.asarray(arg1, dtype=object)
            else:
                arg1 = np.asarray(arg1)
            if len(arg1) and not (
                arg1.ndim == 1 and lib.is_string_array(arg1, skipna=True)
            ):
                raise TypeError(
                    "Invalid arg1 for dtype 'str'. Value should be a "
                    "string or missing arg1 (or array of those)."
                )
        return super()._maybe_convert_setitem_value(arg1)

    def func180(arg0, arg1: ArrayLike) -> npt.NDArray[np.bool_]:
        value_set = [
            pa_scalar.as_py()
            for pa_scalar in [pa.scalar(value, from_pandas=True) for value in arg1]
            if pa_scalar.type in (pa.string(), pa.null(), pa.large_string())
        ]

        # short-circuit to return all False array.
        if not value_set:
            return np.zeros(len(arg0), dtype=bool)

        result = pc.is_in(
            arg0._pa_array, value_set=pa.array(value_set, type=arg0._pa_array.type)
        )
        # pyarrow 2.0.0 returned nulls, so we explicitly specify dtype to convert nulls
        # to False
        return np.array(result, dtype=np.bool_)

    def func180(arg0, arg1, arg2: bool = True):
        arg1 = pandas_dtype(arg1)

        if arg1 == arg0.arg1:
            if arg2:
                return arg0.arg2()
            return arg0
        elif isinstance(arg1, NumericDtype):
            data = arg0._pa_array.cast(pa.from_numpy_dtype(arg1.numpy_dtype))
            return arg1.__from_arrow__(data)
        elif isinstance(arg1, np.arg1) and np.issubdtype(arg1, np.floating):
            return arg0.to_numpy(arg1=arg1, na_value=np.nan)

        return super().astype(arg1, arg2=arg2)

    # ------------------------------------------------------------------------
    # String methods interface

    _str_isalnum = ArrowStringArrayMixin._str_isalnum
    _str_isalpha = ArrowStringArrayMixin._str_isalpha
    _str_isdecimal = ArrowStringArrayMixin._str_isdecimal
    _str_isdigit = ArrowStringArrayMixin._str_isdigit
    _str_islower = ArrowStringArrayMixin._str_islower
    _str_isnumeric = ArrowStringArrayMixin._str_isnumeric
    _str_isspace = ArrowStringArrayMixin._str_isspace
    _str_istitle = ArrowStringArrayMixin._str_istitle
    _str_isupper = ArrowStringArrayMixin._str_isupper

    _str_map = BaseStringArray._str_map
    _str_startswith = ArrowStringArrayMixin._str_startswith
    _str_endswith = ArrowStringArrayMixin._str_endswith
    _str_pad = ArrowStringArrayMixin._str_pad
    _str_lower = ArrowStringArrayMixin._str_lower
    _str_upper = ArrowStringArrayMixin._str_upper
    _str_strip = ArrowStringArrayMixin._str_strip
    _str_lstrip = ArrowStringArrayMixin._str_lstrip
    _str_rstrip = ArrowStringArrayMixin._str_rstrip
    _str_removesuffix = ArrowStringArrayMixin._str_removesuffix
    _str_removeprefix = ArrowStringArrayMixin._str_removeprefix
    _str_find = ArrowStringArrayMixin._str_find
    _str_get = ArrowStringArrayMixin._str_get
    _str_getitem = ArrowStringArrayMixin._str_getitem
    _str_capitalize = ArrowStringArrayMixin._str_capitalize
    _str_title = ArrowStringArrayMixin._str_title
    _str_swapcase = ArrowStringArrayMixin._str_swapcase
    _str_slice_replace = ArrowStringArrayMixin._str_slice_replace
    _str_len = ArrowStringArrayMixin._str_len
    _str_slice = ArrowStringArrayMixin._str_slice

    @staticmethod
    def func180(arg0: str | re.Pattern) -> bool:
        # check if `arg0` is a compiled regex pattern with flags that are not
        # supported by pyarrow
        return (
            isinstance(arg0, re.Pattern)
            and (arg0.flags & ~(re.IGNORECASE | re.UNICODE)) != 0
        )

    @staticmethod
    def _preprocess_re_pattern(
        arg0: str | re.Pattern, case: bool, flags: int
    ) -> tuple[str, bool, int]:
        if isinstance(arg0, re.Pattern):
            pattern = arg0.pattern
            # TODO flags passed separately by user are ignored
            flags = arg0.flags
            # flags is not supported by pyarrow, but `case` is -> extract and remove
            if flags & re.IGNORECASE:
                case = False
                flags = flags & ~re.IGNORECASE
            # when creating a pattern with re.compile and a string, it automatically
            # gets a UNICODE flag, while pyarrow assumes unicode for strings anyway
            flags = flags & ~re.UNICODE
        else:
            pattern = arg0

        if (
            pattern.endswith("\\Z")
            # Second condition counts the number of `\` that patterns ends with
            # prior to Z -> needs to be odd to end with an unescaped \Z
            and (len(pattern) - len(pattern[:-1].rstrip("\\")) + 1) % 2 == 1
        ):
            pattern = pattern[:-2] + "\\z"

        return pattern, case, flags

    def _str_contains(
        self,
        arg0,
        case: bool = True,
        flags: int = 0,
        na=lib.no_default,
        regex: bool = True,
    ):
        if (
            flags
            or self._is_re_pattern_with_flags(arg0)
            or (regex and self._has_unsupported_regex(arg0))
        ):
            return super()._str_contains(arg0, case, flags, na, regex)

        arg0, case, flags = self._preprocess_re_pattern(arg0, case, flags)
        return ArrowStringArrayMixin._str_contains(self, arg0, case, flags, na, regex)

    def _str_match(
        self,
        arg0: str | re.Pattern,
        case: bool = True,
        flags: int = 0,
        na: Scalar | lib.NoDefault = lib.no_default,
    ):
        if (
            flags
            or self._is_re_pattern_with_flags(arg0)
            or self._has_unsupported_regex(arg0)
        ):
            return super()._str_match(arg0, case, flags, na)

        arg0, case, flags = self._preprocess_re_pattern(arg0, case, flags)
        return ArrowStringArrayMixin._str_match(self, arg0, case, flags, na)

    def _str_fullmatch(
        self,
        arg0: str | re.Pattern,
        case: bool = True,
        flags: int = 0,
        na: Scalar | lib.NoDefault = lib.no_default,
    ):
        if (
            flags
            or self._is_re_pattern_with_flags(arg0)
            or self._has_unsupported_regex(arg0)
        ):
            return super()._str_fullmatch(arg0, case, flags, na)

        arg0, case, flags = self._preprocess_re_pattern(arg0, case, flags)
        return ArrowStringArrayMixin._str_fullmatch(self, arg0, case, flags, na)

    def _str_replace(
        self,
        arg0: str | re.Pattern,
        repl: str | Callable,
        n: int = -1,
        case: bool = True,
        flags: int = 0,
        regex: bool = True,
    ):
        if (
            isinstance(arg0, re.Pattern)
            or callable(repl)
            or not case
            or flags
            or (  # substitution contains a named group pattern
                # https://docs.python.org/3/library/re.html
                isinstance(repl, str) and r"\g<" in repl
            )
            or (regex and self._has_unsupported_regex(arg0))
        ):
            return super()._str_replace(arg0, repl, n, case, flags, regex)

        if regex:
            arg0, case, flags = self._preprocess_re_pattern(arg0, case, flags)

        return ArrowStringArrayMixin._str_replace(
            self, arg0, repl, n, case, flags, regex
        )

    def func180(arg0, arg1: int | Sequence[int]):
        if not isinstance(arg1, int):
            return super()._str_repeat(arg1)
        else:
            return ArrowExtensionArray._str_repeat(arg0, arg1=arg1)

    def func180(arg0, arg1: str, arg2: int = 0):
        if arg2 or arg0._has_unsupported_regex(arg1):
            return super()._str_count(arg1, arg2)

        arg1, _, _ = arg0._preprocess_re_pattern(arg1, True, 0)
        result = pc.count_substring_regex(arg0._pa_array, arg1)
        return arg0._convert_int_result(result)

    def func180(arg0, arg1: str = "|", arg2: NpDtype | None = None):
        if arg2 is None:
            arg2 = np.int64
        dummies_pa, labels = ArrowExtensionArray(arg0._pa_array)._str_get_dummies(
            arg1, arg2
        )
        if len(labels) == 0:
            return np.empty(shape=(0, 0), arg2=arg2), labels
        dummies = np.vstack(dummies_pa.to_numpy())
        _dtype = pandas_dtype(arg2)
        dummies_dtype: NpDtype
        if isinstance(_dtype, np.arg2):
            dummies_dtype = _dtype
        else:
            dummies_dtype = np.bool_
        return dummies.astype(dummies_dtype, copy=False), labels

    def func180(arg0, arg1):
        if arg0.dtype.na_value is np.nan:
            arg1 = arg1.cast(pa.int64())
            if isinstance(arg1, pa.Array):
                arg1 = arg1.to_numpy(zero_copy_only=False)
            else:
                arg1 = arg1.to_numpy()
            return arg1

        return Int64Dtype().__from_arrow__(arg1)

    def func180(arg0, arg1):
        if arg0.dtype.na_value is np.nan:
            if isinstance(arg1, pa.Array):
                arg1 = arg1.to_numpy(zero_copy_only=False)
            else:
                arg1 = arg1.to_numpy()
            return arg1.astype("float64", copy=False)

        return Float64Dtype().__from_arrow__(arg1)

    def _reduce(
        arg0, name: str, *, skipna: bool = True, keepdims: bool = False, **kwargs
    ):
        if arg0.dtype.na_value is np.nan and name in ["any", "all"]:
            if not skipna:
                nas = pc.is_null(arg0._pa_array)
                arr = pc.or_kleene(nas, pc.not_equal(arg0._pa_array, ""))
            else:
                arr = pc.not_equal(arg0._pa_array, "")
            arg1 = ArrowExtensionArray(arr)._reduce(
                name, skipna=skipna, keepdims=keepdims, **kwargs
            )
            if keepdims:
                # ArrowExtensionArray will return a length-1 bool[pyarrow] array
                return arg1.astype(np.bool_)
            return arg1

        if name in ("min", "max", "sum", "argmin", "argmax"):
            arg1 = arg0._reduce_calc(name, skipna=skipna, keepdims=keepdims, **kwargs)
        else:
            raise TypeError(f"Cannot perform reduction '{name}' with string dtype")

        if name in ("argmin", "argmax") and isinstance(arg1, pa.Array):
            return arg0._convert_int_result(arg1)
        elif isinstance(arg1, pa.Array):
            return type(arg0)(arg1, dtype=arg0.dtype)
        else:
            return arg1

    def func180(arg0, arg1: bool = True) -> Series:
        result = super().value_counts(arg1=arg1)
        if arg0.dtype.na_value is np.nan:
            res_values = result._values.to_numpy()
            return result._constructor(
                res_values, index=result.index, name=result.name, copy=False
            )
        return result

    def func180(arg0, arg1, arg2):
        if (
            isinstance(arg1, (BaseStringArray, ArrowExtensionArray))
            and arg0.dtype.na_value is not libmissing.NA
            and arg1.dtype.na_value is libmissing.NA
        ):
            # NA has priority of NaN semantics
            return NotImplemented

        result = super()._cmp_method(arg1, arg2)
        if arg0.dtype.na_value is np.nan:
            if arg2 == operator.ne:
                return result.to_numpy(np.bool_, na_value=True)
            else:
                return result.to_numpy(np.bool_, na_value=False)
        return result

    def func180(arg0) -> Self:
        raise TypeError(f"bad operand type for unary +: '{arg0.dtype}'")