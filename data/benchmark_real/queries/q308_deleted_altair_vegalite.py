@magic_arguments.magic_arguments()
@magic_arguments.argument(
    "data",
    nargs="?",
    help="local variablename of a pandas DataFrame to be used as the dataset",
)
@magic_arguments.argument("-v", "--version", dest="version", default="v6")
@magic_arguments.argument("-j", "--json", dest="json", action="store_true")
def vegalite(line, cell) -> vegalite_v6.VegaLite:
    """
    Cell magic for displaying vega-lite visualizations in CoLab.

    %%vegalite [dataframe] [--json] [--version='v6']

    Visualize the contents of the cell using Vega-Lite, optionally
    specifying a pandas DataFrame object to be used as the dataset.

    if --json is passed, then input is parsed as json rather than yaml.
    """
    existing_versions = {"v6": "6"}
    version = existing_versions[args.version]
    assert version in RENDERERS["vega-lite"]
    VegaLite = RENDERERS["vega-lite"][version]
    data_transformers = TRANSFORMERS["vega-lite"][version]

    if args.json:
        spec = json.loads(cell)
    elif not find_spec("yaml"):
        try:
            spec = json.loads(cell)
        except json.JSONDecodeError as err:
            msg = (
                "%%vegalite: spec is not valid JSON. "
                "Install pyyaml to parse spec as yaml"
            )
            raise ValueError(msg) from err
    else:
        import yaml

        spec = yaml.load(cell, Loader=yaml.SafeLoader)

    if args.data is not None:
        data = _get_variable(args.data)
        spec["data"] = _prepare_data(data, data_transformers)

    return VegaLite(spec)