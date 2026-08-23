def sanitize_pandas_dataframe(df: _PandasDataFrameT) -> _PandasDataFrameT:  # noqa: C901
    """
    Sanitize a DataFrame to prepare it for serialization.

    * Make a copy
    * Convert RangeIndex columns to strings
    * Raise ValueError if column names are not strings
    * Raise ValueError if it has a hierarchical index.
    * Convert categoricals to strings.
    * Convert np.bool_ dtypes to Python bool objects
    * Convert np.int dtypes to Python int objects
    * Convert floats to objects and replace NaNs/infs with None.
    * Convert DateTime dtypes into appropriate string representations
    * Convert Nullable integers to objects and replace NaN with None
    * Convert Nullable boolean to objects and replace NaN with None
    * convert dedicated string column to objects and replace NaN with None
    * Raise a ValueError for TimeDelta dtypes
    """
    # This is safe to import here, as this function is only called on pandas input.
    # NumPy is a required dependency of pandas so is also safe to import.
    import numpy as np
    import pandas as pd

    if isinstance(df.columns, pd.RangeIndex):
        df.columns = df.columns.astype(str)
    df = cast("_PandasDataFrameT", df.copy())

    for col_name in df.columns:
        if not isinstance(col_name, str):
            msg = (
                f"Dataframe contains invalid column name: {col_name!r}. "
                "Column names must be strings"
            )
            raise ValueError(msg)

    if isinstance(df.index, pd.MultiIndex):
        msg = "Hierarchical indices not supported"
        raise ValueError(msg)
    if isinstance(df.columns, pd.MultiIndex):
        msg = "Hierarchical indices not supported"
        raise ValueError(msg)

    def to_list_if_array(val):
        if isinstance(val, np.ndarray):
            return val.tolist()
        else:
            return val

    for dtype_item in df.dtypes.items():
        # We know that the column names are strings from the isinstance check
        # further above but mypy thinks it is of type Hashable and therefore does not
        # let us assign it to the col_name variable which is already of type str.
        col_name = cast("str", dtype_item[0])
        dtype = dtype_item[1]
        dtype_name = str(dtype)
        if dtype_name == "category":
            # Work around bug in to_json for categorical types in older versions
            # of pandas as they do not properly convert NaN values to null in to_json.
            # We can probably remove this part once we require pandas >= 1.0
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name in ("string", "str"):
            # dedicated string datatype (since 1.0)
            # https://pandas.pydata.org/pandas-docs/version/1.0.0/whatsnew/v1.0.0.html#dedicated-string-data-type
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name == "bool":
            # convert numpy bools to objects; np.bool is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif dtype_name == "boolean":
            # dedicated boolean datatype (since 1.0)
            # https://pandas.io/docs/user_guide/boolean.html
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name.startswith(("datetime", "timestamp")):
            # Convert datetimes to strings. This needs to be a full ISO string
            # with time, which is why we cannot use ``col.astype(str)``.
            # This is because Javascript parses date-only times in UTC, but
            # parses full ISO-8601 dates as local time, and dates in Vega and
            # Vega-Lite are displayed in local time by default.
            # (see https://github.com/vega/altair/issues/1027)
            df[col_name] = (
                df[col_name].apply(lambda x: x.isoformat()).replace("NaT", "")
            )
        elif dtype_name.startswith("timedelta"):
            msg = (
                f'Field "{col_name}" has type "{dtype}" which is '
                "not supported by Altair. Please convert to "
                "either a timestamp or a numerical value."
                ""
            )
            raise ValueError(msg)
        elif dtype_name.startswith("geometry"):
            # geopandas >=0.6.1 uses the dtype geometry. Continue here
            # otherwise it will give an error on np.issubdtype(dtype, np.integer)
            continue
        elif (
            dtype_name
            in {
                "Int8",
                "Int16",
                "Int32",
                "Int64",
                "UInt8",
                "UInt16",
                "UInt32",
                "UInt64",
                "Float32",
                "Float64",
            }
        ):  # nullable integer datatypes (since 24.0) and nullable float datatypes (since 1.2.0)
            # https://pandas.pydata.org/pandas-docs/version/0.25/whatsnew/v0.24.0.html#optional-integer-na-support
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif numpy_is_subtype(dtype, np.integer):
            # convert integers to objects; np.int is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif numpy_is_subtype(dtype, np.floating):
            # For floats, convert to Python float: np.float is not JSON serializable
            # Also convert NaN/inf values to null, as they are not JSON serializable
            col = df[col_name]
            bad_values = col.isnull() | np.isinf(col)
            df[col_name] = col.astype(object).where(~bad_values, None)
        elif dtype == object:  # noqa: E721
            # Convert numpy arrays saved as objects to lists
            # Arrays are not JSON serializable
            col = df[col_name].astype(object).apply(to_list_if_array)
            df[col_name] = col.where(col.notnull(), None)
    return df