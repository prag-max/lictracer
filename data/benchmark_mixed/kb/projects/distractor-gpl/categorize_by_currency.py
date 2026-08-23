def categorize_by_currency(entry, balances):
    """Group the postings by the currency they declare.

    This is used to prepare the postings for the next stages: Interpolation and
    booking will then be carried out separately on each currency group. At the
    outset of this routine, we should have distinct groups of currencies without
    any ambiguities regarding which currency they need to balance against.

    Here's how this works.

    - First we apply the constraint that cost-currency and price-currency must
      match, if there is both a cost and a price. This reduces the space of
      possibilities somewhat.

    - If the currency is explicitly specified, we put the posting in that
      currency's bucket.

    - If not, we have a few methods left to disambiguate the currency:

      1. We look at the remaining postings... if they are all of a single
         currency, the posting must be in that currency too.

      2. If we cannot do that, we inspect the contents of the inventory of the
         account for the posting. If all the contents are of a single currency,
         we use that one.

    Args:
      entry: A transaction whose incomplete postings to categorize.
      balances: A dict of currency to inventory contents before the transaction is
        applied.
    Returns:
      A list of (currency string, list of tuples) items describing each postings
      and its interpolated currencies, and a list of generated errors for
      currency interpolation. The entry's original postings are left unmodified.
      Each tuple in the value-list contains:
        index: The posting index in the original entry.
        units_currency: The interpolated currency for units.
        cost_currency: The interpolated currency for cost.
        price_currency: The interpolated currency for price.
    """
    errors = []

    groups = collections.defaultdict(list)
    sortdict = {}
    auto_postings = []
    unknown = []
    for index, posting in enumerate(entry.postings):
        units = posting.units
        cost = posting.cost
        price = posting.price

        # Extract and override the currencies locally.
        units_currency = (
            units.currency if units is not MISSING and units is not None else None
        )
        cost_currency = cost.currency if cost is not MISSING and cost is not None else None
        price_currency = (
            price.currency if price is not MISSING and price is not None else None
        )

        # First we apply the constraint that cost-currency and price-currency
        # must match, if there is both a cost and a price. This reduces the
        # space of possibilities somewhat.
        if cost_currency is MISSING and isinstance(price_currency, str):
            cost_currency = price_currency
        if price_currency is MISSING and isinstance(cost_currency, str):
            price_currency = cost_currency

        refer = Refer(index, units_currency, cost_currency, price_currency)

        if units is MISSING and price_currency is None:
            # Bucket auto-postings separately from unknown.
            auto_postings.append(refer)
        else:
            # Bucket with what we know so far.
            currency = get_bucket_currency(refer)
            if currency is not None:
                sortdict.setdefault(currency, index)
                groups[currency].append(refer)
            else:
                # If we need to infer the currency, store in unknown.
                unknown.append(refer)

    # We look at the remaining postings... if they are all of a single currency,
    # the posting must be in that currency too.
    if unknown and len(unknown) == 1 and len(groups) == 1:
        (index, units_currency, cost_currency, price_currency) = unknown.pop()

        other_currency = next(iter(groups.keys()))
        if price_currency is None and cost_currency is None:
            # Infer to the units currency.
            units_currency = other_currency
        else:
            # Infer to the cost and price currencies.
            if price_currency is MISSING:
                price_currency = other_currency
            if cost_currency is MISSING:
                cost_currency = other_currency

        refer = Refer(index, units_currency, cost_currency, price_currency)
        currency = get_bucket_currency(refer)
        assert currency is not None
        sortdict.setdefault(currency, index)
        groups[currency].append(refer)

    # Finally, try to resolve all the unknown legs using the inventory contents
    # of each account.
    for refer in unknown:
        (index, units_currency, cost_currency, price_currency) = refer
        posting = entry.postings[index]
        balance = balances.get(posting.account, None)
        if balance is None:
            balance = inventory.Inventory()

        if units_currency is MISSING:
            balance_currencies = balance.currencies()
            if len(balance_currencies) == 1:
                units_currency = balance_currencies.pop()

        if cost_currency is MISSING or price_currency is MISSING:
            balance_cost_currencies = balance.cost_currencies()
            if len(balance_cost_currencies) == 1:
                balance_cost_currency = balance_cost_currencies.pop()
                if price_currency is MISSING:
                    price_currency = balance_cost_currency
                if cost_currency is MISSING:
                    cost_currency = balance_cost_currency

        refer = Refer(index, units_currency, cost_currency, price_currency)
        currency = get_bucket_currency(refer)
        if currency is not None:
            sortdict.setdefault(currency, index)
            groups[currency].append(refer)
        else:
            errors.append(
                CategorizationError(
                    posting.meta, "Failed to categorize posting {}".format(index + 1), entry
                )
            )

    # Fill in missing units currencies if some remain as missing. This may occur
    # if we used the cost or price to bucket the currency but the units currency
    # was missing.
    for currency, refers in groups.items():
        for rindex, refer in enumerate(refers):
            if refer.units_currency is MISSING:
                posting = entry.postings[refer.index]
                balance = balances.get(posting.account, None)
                if balance is None:
                    continue
                balance_currencies = balance.currencies()
                if len(balance_currencies) == 1:
                    refers[rindex] = refer._replace(units_currency=balance_currencies.pop())

    # Deal with auto-postings.
    if len(auto_postings) > 1:
        refer = auto_postings[-1]
        posting = entry.postings[refer.index]
        errors.append(
            CategorizationError(
                posting.meta,
                "You may not have more than one auto-posting per currency",
                entry,
            )
        )
        auto_postings = auto_postings[0:1]
    for refer in auto_postings:
        for currency, glist in groups.items():
            sortdict.setdefault(currency, refer.index)
            glist.append(Refer(refer.index, currency, None, None))

    # Issue error for all currencies which we could not resolve.
    for currency, refers in groups.items():
        for refer in refers:
            posting = entry.postings[refer.index]
            for currency, name in [
                (refer.units_currency, "units"),
                (refer.cost_currency, "cost"),
                (refer.price_currency, "price"),
            ]:
                if currency is MISSING:
                    errors.append(
                        CategorizationError(
                            posting.meta,
                            "Could not resolve {} currency".format(name),
                            entry,
                        )
                    )

    sorted_groups = sorted(groups.items(), key=lambda item: sortdict[item[0]])
    return sorted_groups, errors