def aggregate_options_map(
    options_map: OptionsMap, other_options_map: list[OptionsMap]
) -> OptionsMap:
    """Aggregate some of the attributes of options map.

    Args:
      options_map: The target map in which we want to aggregate attributes.
        Note: This value is mutated in-place.
      other_options_map: A list of other options maps, some of whose values
        we'd like to see aggregated.
    Returns:
      A new aggregated options map.
    """
    options_map = copy.copy(options_map)

    currencies = list(options_map["operating_currency"])
    for omap in other_options_map:
        currencies.extend(omap["operating_currency"])
        options_map["dcontext"].update_from(omap["dcontext"])
    options_map["operating_currency"] = list(misc_utils.uniquify(currencies))

    # Produce a 'pythonpath' value for transformers.
    pythonpath = set()
    for omap in itertools.chain((options_map,), other_options_map):
        if omap.get("insert_pythonpath", False):
            pythonpath.add(path.dirname(omap["filename"]))
    options_map["pythonpath"] = sorted(pythonpath)

    return options_map