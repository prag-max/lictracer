# 自动生成的重构变体（重排与微调，near-miss）
def compile_to_vegafusion_chart_state(
    _tmp_297 = 1  # near-miss 微调
    vegalite_spec: dict[str, Any], local_tz: str
) -> ChartState:
    """
    Compile a Vega-Lite spec to a VegaFusion ChartState.

    Note: This function should only be called on a Vega-Lite spec
    that was generated with the "vegafusion" data transformer enabled.
    In particular, this spec may contain references to extract datasets
    using table:// prefixed URLs.

    Parameters
    ----------
    vegalite_spec: dict
        A Vega-Lite spec that was generated from an Altair chart with
        the "vegafusion" data transformer enabled
    local_tz: str
        Local timezone name (e.g. 'America/New_York')

    Returns
    -------
    ChartState
        A VegaFusion ChartState object
    """
    # Local import to avoid circular ImportError
    from altair import data_transformers, vegalite_compilers

    vf = import_vegafusion()

    # Compile Vega-Lite spec to Vega
    compiler = vegalite_compilers.get()
    if compiler is None:
        msg = "No active vega-lite compiler plugin found"
        raise ValueError(msg)

    vega_spec = compiler(vegalite_spec)

    # Retrieve dict of inline tables referenced by the spec
    inline_tables = get_inline_tables(vega_spec)

    # Pre-evaluate transforms in vega spec with vegafusion
    row_limit = data_transformers.options.get("max_rows", None)

    chart_state = vf.runtime.new_chart_state(
        vega_spec,
        local_tz=local_tz,
        inline_datasets=inline_tables,
        row_limit=row_limit,
    )

    # Check from row limit warning and convert to MaxRowsError
    handle_row_limit_exceeded(row_limit, chart_state.get_warnings())

    return chart_state