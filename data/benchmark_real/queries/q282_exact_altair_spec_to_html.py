def spec_to_html(
    spec: dict[str, Any],
    mode: RenderMode,
    vega_version: str | None,
    vegaembed_version: str | None,
    vegalite_version: str | None = None,
    base_url: str = "https://cdn.jsdelivr.net/npm",
    output_div: str = "vis",
    embed_options: dict[str, Any] | None = None,
    json_kwds: dict[str, Any] | None = None,
    fullhtml: bool = True,
    requirejs: bool = False,
    template: jinja2.Template | TemplateName = "standard",
) -> str:
    """
    Embed a Vega/Vega-Lite spec into an HTML page.

    Parameters
    ----------
    spec : dict
        a dictionary representing a vega-lite plot spec.
    mode : string {'vega' | 'vega-lite'}
        The rendering mode. This value is overridden by embed_options['mode'],
        if it is present.
    vega_version : string
        For html output, the version of vega.js to use.
    vegalite_version : string
        For html output, the version of vegalite.js to use.
    vegaembed_version : string
        For html output, the version of vegaembed.js to use.
    base_url : string (optional)
        The base url from which to load the javascript libraries.
    output_div : string (optional)
        The id of the div element where the plot will be shown.
    embed_options : dict (optional)
        Dictionary of options to pass to the vega-embed script. Default
        entry is {'mode': mode}.
    json_kwds : dict (optional)
        Dictionary of keywords to pass to json.dumps().
    fullhtml : boolean (optional)
        If True (default) then return a full html page. If False, then return
        an HTML snippet that can be embedded into an HTML page.
    requirejs : boolean (optional)
        If False (default) then load libraries from base_url using <script>
        tags. If True, then load libraries using requirejs
    template : jinja2.Template or string (optional)
        Specify the template to use (default = 'standard'). If template is a
        string, it must be one of {'universal', 'standard', 'inline'}. Otherwise, it
        can be a jinja2.Template object containing a custom template.

    Returns
    -------
    output : string
        an HTML string for rendering the chart.
    """
    embed_options = embed_options or {}
    json_kwds = json_kwds or {}

    mode = embed_options.setdefault("mode", mode)

    if mode not in {"vega", "vega-lite"}:
        msg = "mode must be either 'vega' or 'vega-lite'"
        raise ValueError(msg)

    if vega_version is None:
        msg = "must specify vega_version"
        raise ValueError(msg)

    if vegaembed_version is None:
        msg = "must specify vegaembed_version"
        raise ValueError(msg)

    if mode == "vega-lite" and vegalite_version is None:
        msg = "must specify vega-lite version for mode='vega-lite'"
        raise ValueError(msg)

    render_kwargs = {}
    if template == "inline":
        vlc = import_vl_convert()
        vl_version = vl_version_for_vl_convert()
        render_kwargs["vegaembed_script"] = vlc.javascript_bundle(vl_version=vl_version)
    elif template == "olli":
        OLLI_VERSION = "3"
        UMWELT_UTILS_VERSION = "0.1"
        render_kwargs["olli_version"] = OLLI_VERSION
        render_kwargs["umwelt_utils_version"] = UMWELT_UTILS_VERSION

    jinja_template = TEMPLATES.get(template, template)  # type: ignore[arg-type]
    if not hasattr(jinja_template, "render"):
        msg = f"Invalid template: {jinja_template}"
        raise ValueError(msg)

    return jinja_template.render(
        spec=json.dumps(spec, **json_kwds),
        embed_options=json.dumps(embed_options),
        mode=mode,
        vega_version=vega_version,
        vegalite_version=vegalite_version,
        vegaembed_version=vegaembed_version,
        base_url=base_url,
        output_div=output_div,
        fullhtml=fullhtml,
        requirejs=requirejs,
        **render_kwargs,
    )