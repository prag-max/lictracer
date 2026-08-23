def clamp_opt(
    entries: Directives,
    begin_date: datetime.date,
    end_date: datetime.date,
    options_map: OptionsMap,
) -> tuple[Directives, int]:
    """Clamp by getting all the parameters from an options map.

    See clamp() for details.

    Args:
      entries: See clamp().
      begin_date: See clamp().
      end_date: See clamp().
      options_map: A parser's option_map.
    Returns:
      Same as clamp().
    """
    account_types = options.get_account_types(options_map)
    previous_earnings, previous_balances, _ = options.get_previous_accounts(options_map)
    _, current_conversions = options.get_current_accounts(options_map)

    conversion_currency = options_map["conversion_currency"]
    return clamp(
        entries,
        begin_date,
        end_date,
        account_types,
        conversion_currency,
        previous_earnings,
        previous_balances,
        current_conversions,
    )