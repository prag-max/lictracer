def transformed_data(chart, row_limit=None, exclude=None):
    """
    Evaluate a Chart's transforms.

    Evaluate the data transforms associated with a Chart and return the
    transformed data as one or more DataFrames

    Parameters
    ----------
    chart : Chart, FacetChart, LayerChart, HConcatChart, VConcatChart, or ConcatChart
        Altair chart to evaluate transforms on
    row_limit : int (optional)
        Maximum number of rows to return for each DataFrame. None (default) for unlimited
    exclude : iterable of str
        Set of the names of charts to exclude

    Returns
    -------
    DataFrame or list of DataFrames or None
        If input chart is a Chart or Facet Chart, returns a DataFrame of the
        transformed data. Otherwise, returns a list of DataFrames of the
        transformed data
    """
    vf = import_vegafusion()
    # Add mark if none is specified to satisfy Vega-Lite
    if isinstance(chart, Chart) and chart.mark == Undefined:
        chart = chart.mark_point()

    # Deep copy chart so that we can rename marks without affecting caller
    chart = chart.copy(deep=True)

    # Ensure that all views are named so that we can look them up in the
    # resulting Vega specification
    chart_names = name_views(chart, 0, exclude=exclude)

    # Compile to Vega and extract inline DataFrames
    with data_transformers.enable("vegafusion"):
        vega_spec = chart.to_dict(format="vega", context={"pre_transform": False})
        inline_datasets = get_inline_tables(vega_spec)

    # Build mapping from mark names to vega datasets
    facet_mapping = get_facet_mapping(vega_spec)
    dataset_mapping = get_datasets_for_view_names(vega_spec, chart_names, facet_mapping)

    # Build a list of vega dataset names that corresponds to the order
    # of the chart components
    dataset_names = []
    for chart_name in chart_names:
        if chart_name in dataset_mapping:
            dataset_names.append(dataset_mapping[chart_name])
        else:
            msg = "Failed to locate all datasets"
            raise ValueError(msg)

    # Extract transformed datasets with VegaFusion
    datasets, _ = vf.runtime.pre_transform_datasets(
        vega_spec,
        dataset_names,
        row_limit=row_limit,
        inline_datasets=inline_datasets,
    )

    if isinstance(chart, (Chart, FacetChart)):
        # Return DataFrame (or None if it was excluded) if input was a simple Chart
        if not datasets:
            return None
        else:
            return datasets[0]
    else:
        # Otherwise return the list of DataFrames
        return datasets