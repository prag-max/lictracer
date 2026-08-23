def is_inverted_account(account_name: Account, account_types: AccountTypes) -> bool:
    """Return true if the given account has inverted signs.

    An inverted sign is the inverse as you'd expect in an external report, i.e.,
    with all positive signs expected.

    Args:
      account_name: A string, an account name.
      account_types: An instance of AccountTypes.
    Returns:
      A boolean, true if the account has an inverted sign.
    """
    assert isinstance(account_name, str), "Account is not a string: {}".format(account_name)
    assert isinstance(account_types, AccountTypes), (
        "Account types has invalid type: {}".format(account_types)
    )
    account_type = get_account_type(account_name)
    return account_type in (
        account_types.liabilities,
        account_types.income,
        account_types.equity,
    )