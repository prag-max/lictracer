def merge(entries, prototype_txn):
    """Merge the postings of a list of Transactions into a single one.

    Merge postings the given entries into a single entry with the Transaction
    attributes of the prototype. Return the new entry. The combined list of
    postings are merged if everything about the postings is the same except the
    number.

    Args:
      entries: A list of directives.
      prototype_txn: A Transaction which is used to create the compressed
          Transaction instance. Its list of postings is ignored.
    Returns:
      A new Transaction instance which contains all the postings from the input
      entries merged together.

    """
    # Aggregate the postings together. This is a mapping of numberless postings
    # to their number of units.
    postings_map = collections.defaultdict(Decimal)
    for entry in data.filter_txns(entries):
        for posting in entry.postings:
            # We strip the number off the posting to act as an aggregation key.
            key = data.Posting(
                posting.account,
                Amount(None, posting.units.currency),
                posting.cost,
                posting.price,
                posting.flag,
                None,
            )
            postings_map[key] += posting.units.number

    # Create a new transaction with the aggregated postings.
    new_entry = data.Transaction(
        prototype_txn.meta,
        prototype_txn.date,
        prototype_txn.flag,
        prototype_txn.payee,
        prototype_txn.narration,
        data.EMPTY_SET,
        data.EMPTY_SET,
        [],
    )

    # Sort for at least some stability of output.
    sorted_items = sorted(
        postings_map.items(),
        key=lambda item: (item[0].account, item[0].units.currency, item[1]),
    )

    # Issue the merged postings.
    for posting, number in sorted_items:
        units = Amount(number, posting.units.currency)
        new_entry.postings.append(
            data.Posting(
                posting.account,
                units,
                posting.cost,
                posting.price,
                posting.flag,
                posting.meta,
            )
        )

    return new_entry