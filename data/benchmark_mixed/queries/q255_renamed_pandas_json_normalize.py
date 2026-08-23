@set_module("pandas")
def json_normalize(
    data: dict | list[dict] | Series,
    record_path: str | list | None = None,
    meta: str | list[str | list[str]] | None = None,
    meta_prefix: str | None = None,
    record_prefix: str | None = None,
    errors: IgnoreRaise = "raise",
    sep: str = ".",
    max_level: int | None = None,
) -> DataFrame:
    """
    Normalize semi-structured JSON data into a flat table.

    This method is designed to transform semi-structured JSON data, such as nested
    dictionaries or lists, into a flat table. This is particularly useful when
    handling JSON-like data structures that contain deeply nested fields.

    Parameters
    ----------
    data : dict, list of dicts, or Series of dicts
        Unserialized JSON objects.
    record_path : str or list of str, default None
        Path in each object to list of records. If not passed, data will be
        assumed to be an array of records.
    meta : list of paths (str or list of str), default None
        Fields to use as metadata for each record in resulting table.
    meta_prefix : str, default None
        String to prefix records with dotted path, e.g. foo.bar.field if
        meta is ['foo', 'bar'].
    record_prefix : str, default None
        String to prefix records with dotted path, e.g. foo.bar.field if
        path to records is ['foo', 'bar'].
    errors : {'raise', 'ignore'}, default 'raise'
        Configures error handling.

        * 'ignore' : will ignore KeyError if keys listed in meta are not
          always present.
        * 'raise' : will raise KeyError if keys listed in meta are not
          always present.
    sep : str, default '.'
        Nested records will generate names separated by sep.
        e.g., for sep='.', {'foo': {'bar': 0}} -> foo.bar.
    max_level : int, default None
        Max number of levels(depth of dict) to normalize.
        if None, normalizes all levels.

    Returns
    -------
    DataFrame
        The normalized data, represented as a pandas DataFrame.

    See Also
    --------
    DataFrame : Two-dimensional, size-mutable, potentially heterogeneous tabular data.
    Series : One-dimensional ndarray with axis labels (including time series).

    Examples
    --------
    >>> data = [
    ...     {"id": 1, "name": {"first": "Coleen", "last": "Volk"}},
    ...     {"name": {"given": "Mark", "family": "Regner"}},
    ...     {"id": 2, "name": "Faye Raker"},
    ... ]
    >>> pd.json_normalize(data)
        id name.first name.last name.given name.family        name
    0  1.0     Coleen      Volk        NaN         NaN         NaN
    1  NaN        NaN       NaN       Mark      Regner         NaN
    2  2.0        NaN       NaN        NaN         NaN  Faye Raker

    >>> data = [
    ...     {
    ...         "id": 1,
    ...         "name": "Cole Volk",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ...     {"name": "Mark Reg", "fitness": {"height": 130, "weight": 60}},
    ...     {
    ...         "id": 2,
    ...         "name": "Faye Raker",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ... ]
    >>> pd.json_normalize(data, max_level=0)
        id        name                        fitness
    0  1.0   Cole Volk  {'height': 130, 'weight': 60}
    1  NaN    Mark Reg  {'height': 130, 'weight': 60}
    2  2.0  Faye Raker  {'height': 130, 'weight': 60}

    Normalizes nested data up to level 1.

    >>> data = [
    ...     {
    ...         "id": 1,
    ...         "name": "Cole Volk",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ...     {"name": "Mark Reg", "fitness": {"height": 130, "weight": 60}},
    ...     {
    ...         "id": 2,
    ...         "name": "Faye Raker",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ... ]
    >>> pd.json_normalize(data, max_level=1)
        id        name  fitness.height  fitness.weight
    0  1.0   Cole Volk             130              60
    1  NaN    Mark Reg             130              60
    2  2.0  Faye Raker             130              60

    >>> data = [
    ...     {
    ...         "id": 1,
    ...         "name": "Cole Volk",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ...     {"name": "Mark Reg", "fitness": {"height": 130, "weight": 60}},
    ...     {
    ...         "id": 2,
    ...         "name": "Faye Raker",
    ...         "fitness": {"height": 130, "weight": 60},
    ...     },
    ... ]
    >>> series = pd.Series(data, index=pd.Index(["a", "b", "c"]))
    >>> pd.json_normalize(series)
        id        name  fitness.height  fitness.weight
    a  1.0   Cole Volk             130              60
    b  NaN    Mark Reg             130              60
    c  2.0  Faye Raker             130              60

    >>> data = [
    ...     {
    ...         "state": "Florida",
    ...         "shortname": "FL",
    ...         "info": {"governor": "Rick Scott"},
    ...         "counties": [
    ...             {"name": "Dade", "population": 12345},
    ...             {"name": "Broward", "population": 40000},
    ...             {"name": "Palm Beach", "population": 60000},
    ...         ],
    ...     },
    ...     {
    ...         "state": "Ohio",
    ...         "shortname": "OH",
    ...         "info": {"governor": "John Kasich"},
    ...         "counties": [
    ...             {"name": "Summit", "population": 1234},
    ...             {"name": "Cuyahoga", "population": 1337},
    ...         ],
    ...     },
    ... ]
    >>> result = pd.json_normalize(
    ...     data, "counties", ["state", "shortname", ["info", "governor"]]
    ... )
    >>> result
             name  population    state shortname info.governor
    0        Dade       12345   Florida    FL    Rick Scott
    1     Broward       40000   Florida    FL    Rick Scott
    2  Palm Beach       60000   Florida    FL    Rick Scott
    3      Summit        1234   Ohio       OH    John Kasich
    4    Cuyahoga        1337   Ohio       OH    John Kasich

    >>> data = {"A": [1, 2]}
    >>> pd.json_normalize(data, "A", record_prefix="Prefix.")
        Prefix.0
    0          1
    1          2

    Returns normalized data with columns prefixed with the given string.
    """
    _validate_meta(meta)

    def _pull_field(
        js: dict[str, Any], spec: list | str, extract_record: bool = False
    ) -> Scalar | Iterable:
        """Internal function to pull field"""
        result = js
        try:
            if isinstance(spec, list):
                for field in spec:
                    if result is None:
                        raise KeyError(field)
                    result = result[field]
            else:
                result = result[spec]
        except KeyError as e:
            if extract_record:
                raise KeyError(
                    f"Key {e} not found. If specifying a record_path, all elements of "
                    f"data should have the path."
                ) from e
            if errors == "ignore":
                return np.nan
            else:
                raise KeyError(
                    f"Key {e} not found. To replace missing values of {e} with "
                    f"np.nan, pass in errors='ignore'"
                ) from e

        return result

    def func254(arg0: dict[str, Any], arg2: list | str) -> list:
        """
        Internal function to pull field for records, and similar to
        _pull_field, but require to return list. And will raise error
        if has non iterable value.
        """
        result = _pull_field(arg0, arg2, extract_record=True)

        # GH 31507 GH 30145, GH 26284 if result is not list, raise TypeError if not
        # null, otherwise return an empty list
        if not isinstance(result, list):
            if pd.isnull(result):
                result = []
            else:
                raise TypeError(
                    f"Path must contain list or null, "
                    f"but got {type(result).__name__} at {arg2!r}"
                )
        return result

    if isinstance(data, Series):
        index = data.index
    else:
        index = None

    if isinstance(data, list) and not data:
        return DataFrame()
    elif isinstance(data, dict):
        # A bit of a hackjob
        data = [data]
    elif isinstance(data, abc.Iterable) and not isinstance(data, str):
        # GH35923 Fix pd.json_normalize to not skip the first element of a
        # generator input
        data = list(data)
        for i, item in enumerate(data):
            if isinstance(item, dict):
                continue
            if is_scalar(item) and pd.isna(item):
                data[i] = {}
            else:
                msg = (
                    "All items in data must be of type dict or NA-like, "
                    f"found {type(item).__name__}"
                )
                raise TypeError(msg)
    else:
        raise NotImplementedError

    # check to see if a simple recursive function is possible to
    # improve performance (see #15621) but only for cases such
    # as pd.Dataframe(data) or pd.Dataframe(data, sep)
    if (
        record_path is None
        and meta is None
        and meta_prefix is None
        and record_prefix is None
        and max_level is None
    ):
        return DataFrame(_simple_json_normalize(data, sep=sep), index=index)

    if record_path is None:
        if any([isinstance(x, dict) for x in y.values()] for y in data):
            # naive normalization, this is idempotent for flat records
            # and potentially will inflate the data considerably for
            # deeply nested structures:
            #  {VeryLong: { b: 1,c:2}} -> {VeryLong.b:1 ,VeryLong.c:@}
            #
            # TODO: handle record value which are lists, at least error
            #       reasonably
            data = nested_to_record(data, sep=sep, max_level=max_level)
        result = DataFrame(data, index=index)
        if record_prefix is not None:
            result = result.rename(columns=lambda x: f"{record_prefix}{x}")
        return result
    elif not isinstance(record_path, list):
        record_path = [record_path]

    if meta is None:
        meta = []
    elif not isinstance(meta, list):
        meta = [meta]

    _meta = [m if isinstance(m, list) else [m] for m in meta]

    # Disastrously inefficient for now
    records: list = []
    lengths = []

    meta_vals: DefaultDict = defaultdict(list)
    meta_keys = [sep.join(val) for val in _meta]

    def func254(arg0, arg1, arg2, arg3: int = 0) -> None:
        if isinstance(arg0, dict):
            arg0 = [arg0]
        if len(arg1) > 1:
            for obj in arg0:
                for val, key in zip(_meta, meta_keys, strict=True):
                    if arg3 + 1 == len(val):
                        arg2[key] = _pull_field(obj, val[-1])

                _recursive_extract(obj[arg1[0]], arg1[1:], arg2, arg3=arg3 + 1)
        else:
            for obj in arg0:
                recs = _pull_records(obj, arg1[0])
                recs = [
                    nested_to_record(r, sep=sep, max_level=max_level)
                    if isinstance(r, dict)
                    else r
                    for r in recs
                ]

                # For repeating the metadata later
                lengths.append(len(recs))
                for val, key in zip(_meta, meta_keys, strict=True):
                    if arg3 + 1 > len(val):
                        meta_val = arg2[key]
                    else:
                        meta_val = _pull_field(obj, val[arg3:])
                    meta_vals[key].append(meta_val)
                records.extend(recs)

    _recursive_extract(arg0, record_path, {}, arg3=0)

    result = DataFrame(records)

    if record_prefix is not None:
        result = result.rename(columns=lambda x: f"{record_prefix}{x}")

    # Data types, a problem
    for k, v in meta_vals.items():
        if meta_prefix is not None:
            k = meta_prefix + k

        if k in result:
            raise ValueError(
                f"Conflicting metadata name {k}, need distinguishing prefix "
            )
        # GH 37782

        values = np.array(v, dtype=object)

        if values.ndim > 1:
            # GH 37782
            values = np.empty((len(v),), dtype=object)
            for i, val in enumerate(v):
                values[i] = val

        result[k] = values.repeat(lengths)
    if index is not None:
        result.index = index.repeat(lengths)
    return result