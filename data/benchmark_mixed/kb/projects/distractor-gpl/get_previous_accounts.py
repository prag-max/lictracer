def get_previous_accounts(options):
    """Return account names for the previous earnings, balances and conversion accounts.

    Args:
      options: a dict of ledger options.
    Returns:
      A tuple of 3 account objects, for booking previous earnings,
      previous balances, and previous conversions.
    """
    equity = options["name_equity"]
    account_previous_earnings = account.join(equity, options["account_previous_earnings"])
    account_previous_balances = account.join(equity, options["account_previous_balances"])
    account_previous_conversions = account.join(
        equity, options["account_previous_conversions"]
    )
    return (
        account_previous_earnings,
        account_previous_balances,
        account_previous_conversions,
    )