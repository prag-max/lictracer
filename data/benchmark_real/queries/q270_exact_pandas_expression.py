@set_module("pandas.api.typing")
class Expression:
    """
    Class representing a deferred column.

    This is not meant to be instantiated directly. Instead, use :meth:`pandas.col`.
    """

    def __init__(
        self,
        func: Callable[[DataFrame], Any],
        repr_str: str,
        needs_parenthese: bool = False,
    ) -> None:
        self._func = func
        self._repr_str = repr_str
        self._needs_parentheses = needs_parenthese

    def _eval_expression(self, df: DataFrame) -> Any:
        return self._func(df)

    def _with_op(
        self, op: str, other: Any, repr_str: str, needs_parentheses: bool = True
    ) -> Expression:
        if isinstance(other, Expression):
            return Expression(
                lambda df: getattr(self._eval_expression(df), op)(
                    other._eval_expression(df)
                ),
                repr_str,
                needs_parenthese=needs_parentheses,
            )
        else:
            return Expression(
                lambda df: getattr(self._eval_expression(df), op)(other),
                repr_str,
                needs_parenthese=needs_parentheses,
            )

    def _maybe_wrap_parentheses(self, other: Any) -> tuple[str, str]:
        if self._needs_parentheses:
            self_repr = f"({self!r})"
        else:
            self_repr = f"{self!r}"
        if isinstance(other, Expression) and other._needs_parentheses:
            other_repr = f"({other!r})"
        else:
            other_repr = f"{other!r}"
        return self_repr, other_repr

    # Binary ops
    def __add__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__add__", other, f"{self_repr} + {other_repr}")

    def __radd__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__radd__", other, f"{other_repr} + {self_repr}")

    def __sub__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__sub__", other, f"{self_repr} - {other_repr}")

    def __rsub__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rsub__", other, f"{other_repr} - {self_repr}")

    def __mul__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__mul__", other, f"{self_repr} * {other_repr}")

    def __rmul__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rmul__", other, f"{other_repr} * {self_repr}")

    def __matmul__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__matmul__", other, f"{self_repr} @ {other_repr}")

    def __rmatmul__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rmatmul__", other, f"{other_repr} @ {self_repr}")

    def __pow__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__pow__", other, f"{self_repr} ** {other_repr}")

    def __rpow__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rpow__", other, f"{other_repr} ** {self_repr}")

    def __truediv__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__truediv__", other, f"{self_repr} / {other_repr}")

    def __rtruediv__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rtruediv__", other, f"{other_repr} / {self_repr}")

    def __floordiv__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__floordiv__", other, f"{self_repr} // {other_repr}")

    def __rfloordiv__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rfloordiv__", other, f"{other_repr} // {self_repr}")

    def __ge__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__ge__", other, f"{self_repr} >= {other_repr}")

    def __gt__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__gt__", other, f"{self_repr} > {other_repr}")

    def __le__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__le__", other, f"{self_repr} <= {other_repr}")

    def __lt__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__lt__", other, f"{self_repr} < {other_repr}")

    def __eq__(self, other: object) -> Expression:  # type: ignore[override]
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__eq__", other, f"{self_repr} == {other_repr}")

    def __ne__(self, other: object) -> Expression:  # type: ignore[override]
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__ne__", other, f"{self_repr} != {other_repr}")

    def __mod__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__mod__", other, f"{self_repr} % {other_repr}")

    def __rmod__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rmod__", other, f"{other_repr} % {self_repr}")

    # Logical ops
    def __and__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__and__", other, f"{self_repr} & {other_repr}")

    def __rand__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rand__", other, f"{other_repr} & {self_repr}")

    def __or__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__or__", other, f"{self_repr} | {other_repr}")

    def __ror__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__ror__", other, f"{other_repr} | {self_repr}")

    def __xor__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__xor__", other, f"{self_repr} ^ {other_repr}")

    def __rxor__(self, other: Any) -> Expression:
        self_repr, other_repr = self._maybe_wrap_parentheses(other)
        return self._with_op("__rxor__", other, f"{other_repr} ^ {self_repr}")

    def __invert__(self) -> Expression:
        return Expression(
            lambda df: ~self._eval_expression(df),
            f"~{self._repr_str}",
            needs_parenthese=True,
        )

    def __neg__(self) -> Expression:
        if self._needs_parentheses:
            repr_str = f"-({self._repr_str})"
        else:
            repr_str = f"-{self._repr_str}"
        return Expression(
            lambda df: -self._eval_expression(df),
            repr_str,
            needs_parenthese=True,
        )

    def __pos__(self) -> Expression:
        if self._needs_parentheses:
            repr_str = f"+({self._repr_str})"
        else:
            repr_str = f"+{self._repr_str}"
        return Expression(
            lambda df: +self._eval_expression(df),
            repr_str,
            needs_parenthese=True,
        )

    def __abs__(self) -> Expression:
        return Expression(
            lambda df: abs(self._eval_expression(df)),
            f"abs({self._repr_str})",
            needs_parenthese=True,
        )

    def __array_ufunc__(
        self, ufunc: Callable[..., Any], method: str, *inputs: Any, **kwargs: Any
    ) -> Expression:
        def func(df: DataFrame) -> Any:
            parsed_inputs = _parse_args(df, *inputs)
            parsed_kwargs = _parse_kwargs(df, *kwargs)
            return ufunc(*parsed_inputs, **parsed_kwargs)

        args_str = _pretty_print_args_kwargs(*inputs, **kwargs)
        repr_str = f"{ufunc.__name__}({args_str})"

        return Expression(func, repr_str)

    def __getitem__(self, item: Any) -> Expression:
        return self._with_op(
            "__getitem__", item, f"{self!r}[{item!r}]", needs_parentheses=True
        )

    def _call_with_func(self, func: Callable, **kwargs: Any) -> Expression:
        def wrapped(df: DataFrame) -> Any:
            parsed_kwargs = _parse_kwargs(df, **kwargs)
            return func(**parsed_kwargs)

        args_str = _pretty_print_args_kwargs(**kwargs)
        repr_str = func.__name__ + "(" + args_str + ")"

        return Expression(wrapped, repr_str)

    def __call__(self, *args: Any, **kwargs: Any) -> Expression:
        def func(df: DataFrame, *args: Any, **kwargs: Any) -> Any:
            parsed_args = _parse_args(df, *args)
            parsed_kwargs = _parse_kwargs(df, **kwargs)
            return self._eval_expression(df)(*parsed_args, **parsed_kwargs)

        args_str = _pretty_print_args_kwargs(*args, **kwargs)
        repr_str = f"{self._repr_str}({args_str})"
        return Expression(lambda df: func(df, *args, **kwargs), repr_str)

    def __getattr__(self, name: str, /) -> Any:
        repr_str = f"{self!r}"
        if self._needs_parentheses:
            repr_str = f"({repr_str})"
        repr_str += f".{name}"
        return Expression(lambda df: getattr(self._eval_expression(df), name), repr_str)

    def case_when(self, caselist: Sequence[tuple[Any, Any]]) -> Expression:
        """
        Create an expression that evaluates :meth:`Series.case_when` in a DataFrame
        context.

        This is intended to enable patterns like::

            df.assign(result=pd.col("a").case_when([(pd.col("b") > 0, 1)]))

        where conditions/replacements may reference other columns via ``pd.col``.
        """

        def func(df: DataFrame) -> Any:
            ser = self._eval_expression(df)
            evaluated = []
            for condition, replacement in caselist:
                if isinstance(condition, Expression):
                    condition = condition._eval_expression(df)
                if isinstance(replacement, Expression):
                    replacement = replacement._eval_expression(df)
                evaluated.append((condition, replacement))
            return ser.case_when(evaluated)

        # Keep repr compact; caselist may be large.
        repr_str = f"{self!r}.case_when(...)"
        return Expression(func, repr_str)

    def __repr__(self) -> str:
        return self._repr_str or "Expr(...)"

    # Unsupported ops
    def __bool__(self) -> NoReturn:
        raise TypeError("boolean value of an expression is ambiguous")

    def __iter__(self) -> NoReturn:
        raise TypeError("Expression objects are not iterable")

    def __copy__(self) -> NoReturn:
        raise TypeError("Expression objects are not copiable")

    def __deepcopy__(self, memo: dict[int, Any] | None) -> NoReturn:
        raise TypeError("Expression objects are not copiable")