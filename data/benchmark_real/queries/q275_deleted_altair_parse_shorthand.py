def parse_shorthand(  # noqa: C901
    shorthand: dict[str, Any] | str,
    data: IntoDataFrame | None = None,
    parse_aggregates: bool = True,
    parse_window_ops: bool = False,
    parse_timeunits: bool = True,
    parse_types: bool = True,
) -> dict[str, Any]:
    """
    General tool to parse shorthand values.

    These are of the form:

    - "col_name"
    - "col_name:O"
    - "average(col_name)"
    - "average(col_name):O"

    Optionally, a dataframe may be supplied, from which the type
    will be inferred if not specified in the shorthand.

    Parameters
    ----------
    shorthand : dict or string
        The shorthand representation to be parsed
    data : DataFrame, optional
        If specified and of type DataFrame, then use these values to infer the
        column type if not provided by the shorthand.
    parse_aggregates : boolean
        If True (default), then parse aggregate functions within the shorthand.
    parse_window_ops : boolean
        If True then parse window operations within the shorthand (default:False)
    parse_timeunits : boolean
        If True (default), then parse timeUnits from within the shorthand
    parse_types : boolean
        If True (default), then parse typecodes within the shorthand

    Returns
    -------
    attrs : dict
        a dictionary of attributes extracted from the shorthand

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({"foo": ["A", "B", "A", "B"], "bar": [1, 2, 3, 4]})

    >>> parse_shorthand("name") == {"field": "name"}
    True

    >>> parse_shorthand("name:Q") == {"field": "name", "type": "quantitative"}
    True

    >>> parse_shorthand("average(col)") == {"aggregate": "average", "field": "col"}
    True

    >>> parse_shorthand("foo:O") == {"field": "foo", "type": "ordinal"}
    True

    >>> parse_shorthand("min(foo):Q") == {
    ...     "aggregate": "min",
    ...     "field": "foo",
    ...     "type": "quantitative",
    ... }
    True

    >>> parse_shorthand("month(col)") == {
    ...     "field": "col",
    ...     "timeUnit": "month",
    ...     "type": "temporal",
    ... }
    True

    >>> parse_shorthand("year(col):O") == {
    ...     "field": "col",
    ...     "timeUnit": "year",
    ...     "type": "ordinal",
    ... }
    True

    >>> parse_shorthand("foo", data) == {"field": "foo", "type": "nominal"}
    True

    >>> parse_shorthand("bar", data) == {"field": "bar", "type": "quantitative"}
    True

    >>> parse_shorthand("bar:O", data) == {"field": "bar", "type": "ordinal"}
    True

    >>> parse_shorthand("sum(bar)", data) == {
    ...     "aggregate": "sum",
    ...     "field": "bar",
    ...     "type": "quantitative",
    ... }
    True

    >>> parse_shorthand("count()", data) == {
    ...     "aggregate": "count",
    ...     "type": "quantitative",
    ... }
    True
    """

    if not shorthand:
        return {}

    patterns = []

    if parse_aggregates:
        patterns.extend([r"{agg_count}\(\)"])
        patterns.extend([r"{aggregate}\({field}\)"])
    if parse_window_ops:
        patterns.extend([r"{op_count}\(\)"])
        patterns.extend([r"{window_op}\({field}\)"])
    if parse_timeunits:
        patterns.extend([r"{timeUnit}\({field}\)"])

    patterns.extend([r"{field}"])

    if parse_types:
        patterns = list(itertools.chain(*((p + ":{type}", p) for p in patterns)))

    regexps = (
        re.compile(r"\A" + p.format(**SHORTHAND_UNITS) + r"\Z", re.DOTALL)
        for p in patterns
    )

    # find matches depending on valid fields passed
    if isinstance(shorthand, dict):
        attrs = shorthand
    else:
        attrs = next(
            exp.match(shorthand).groupdict()  # type: ignore[union-attr]
            for exp in regexps
            if exp.match(shorthand) is not None
        )

    # Handle short form of the type expression
    if "type" in attrs:
        attrs["type"] = INV_TYPECODE_MAP.get(attrs["type"], attrs["type"])

    # counts are quantitative by default
    if attrs == {"aggregate": "count"}:
        attrs["type"] = "quantitative"

    # times are temporal by default
    if "timeUnit" in attrs and "type" not in attrs:
        attrs["type"] = "temporal"

    # if data is specified and type is not, infer type from data
    if "type" not in attrs and is_data_type(data):
        unescaped_field = attrs["field"].replace("\\", "")
        data_nw = nw.from_native(data, eager_or_interchange_only=True)
        schema = data_nw.schema
        if unescaped_field in schema:
            column = data_nw[unescaped_field]
            if schema[unescaped_field] in {
                nw.Object,
                nw.Unknown,
            } and is_pandas_dataframe(data_nw.to_native()):
                attrs["type"] = infer_vegalite_type_for_pandas(column.to_native())
            else:
                attrs["type"] = infer_vegalite_type_for_narwhals(column)
            if isinstance(attrs["type"], tuple):
                attrs["sort"] = attrs["type"][1]
                attrs["type"] = attrs["type"][0]

    # If an unescaped colon is still present, it's often due to an incorrect data type specification
    # but could also be due to using a column name with ":" in it.
    if (
        "field" in attrs
        and ":" in attrs["field"]
        and attrs["field"][attrs["field"].rfind(":") - 1] != "\\"
    ):
        raise ValueError(
            '"{}" '.format(attrs["field"].split(":")[-1])
            + "is not one of the valid encoding data types: {}.".format(
                ", ".join(TYPECODE_MAP.values())
            )
            + "\nFor more details, see https://altair-viz.github.io/user_guide/encodings/index.html#encoding-data-types. "
            + "If you are trying to use a column name that contains a colon, "
            + 'prefix it with a backslash; for example "column\\:name" instead of "column:name".'
        )
    return attrs