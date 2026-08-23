def sub(amount1: Amount, amount2: Amount) -> Amount:
    """Subtract the given amounts with the same currency.

    Args:
      amount1: An instance of Amount.
      amount2: An instance of Amount.
    Returns:
      An instance of Amount, with the difference between the two amount's
      numbers, in the same currency.
    """
    assert isinstance(amount1.number, Decimal), (
        "Amount1's number is not a Decimal instance: {}".format(amount1.number)
    )
    assert isinstance(amount2.number, Decimal), (
        "Amount2's number is not a Decimal instance: {}".format(amount2.number)
    )
    if amount1.currency != amount2.currency:
        raise ValueError(
            "Unmatching currencies for operation on {} and {}".format(amount1, amount2)
        )
    return Amount(amount1.number - amount2.number, amount1.currency)