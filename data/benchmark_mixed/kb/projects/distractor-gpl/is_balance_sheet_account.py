def is_balance_sheet_account(account_name: Account, account_types: AccountTypes) -> bool:
    """Return true if the given account is a balance sheet account.
    Assets, liabilities and equity accounts are balance sheet accounts.

    Args:
      account_name: A string, an account name.
      account_types: An instance of AccountTypes.
    Returns:
      A boolean, true if the account is a balance sheet account.
    """
    assert isinstance(account_name, str), "Account is not a string: {}".format(account_name)
    assert isinstance(account_types, AccountTypes), (
        "Account types has invalid type: {}".format(account_types)
    )
    account_type = get_account_type(account_name)
    return account_type in (
        account_types.assets,
        account_types.liabilities,
        account_types.equity,
    )