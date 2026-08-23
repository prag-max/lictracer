def interpolate_group(postings, balances, currency, tolerances):
    """Interpolate missing numbers in the set of postings.

    Args:
      postings: A list of Posting instances.
      balances: A dict of account to its ante-inventory.
      currency: The weight currency of this group, used for reporting errors.
      tolerances: A dict of currency to tolerance values.
    Returns:
      A tuple of
        postings: A list of new posting instances.
        errors: A list of errors generated during interpolation.
        interpolated: A boolean, true if we did have to interpolate.

      In the case of an error, this returns the original list of postings, which
      is still incomplete. If an error is returned, you should probably skip the
      transaction altogether, or just not include the postings in it. (An
      alternative behaviour would be to return only the list of valid postings,
      but that would likely result in an unbalanced transaction. We do it this
      way by choice.)
    """
    errors = []

    # Figure out which type of amount is missing, by creating a list of
    # incomplete postings and which type of units is missing.
    incomplete = []
    for index, posting in enumerate(postings):
        units = posting.units
        cost = posting.cost
        price = posting.price

        # Identify incomplete parts of the Posting components.
        if units.number is MISSING:
            incomplete.append((MissingType.UNITS, index))

        if isinstance(cost, CostSpec):
            if cost and cost.number_per is MISSING:
                incomplete.append((MissingType.COST_PER, index))
            if cost and cost.number_total is MISSING:
                incomplete.append((MissingType.COST_TOTAL, index))
        else:
            # Check that a resolved instance of Cost never needs interpolation.
            #
            # Note that in theory we could support the interpolation of regular
            # per-unit costs in these if we wanted to; but because they're all
            # reducing postings that have been booked earlier, those never need
            # to be interpolated.
            if cost is not None:
                assert isinstance(cost.number, Decimal), (
                    "Internal error: cost has no number: {}; on postings: {}".format(
                        cost, postings
                    )
                )

        if price and price.number is MISSING:
            incomplete.append((MissingType.PRICE, index))

    # The replacement posting for the incomplete posting of this group.
    new_posting = None

    if len(incomplete) == 0:
        # If there are no missing numbers, just convert the CostSpec to Cost and
        # return that.
        out_postings = [convert_costspec_to_cost(posting) for posting in postings]

    elif len(incomplete) > 1:
        # If there is more than a single value to be interpolated, generate an
        # error and return no postings.
        _, posting_index = incomplete[0]
        errors.append(
            InterpolationError(
                postings[posting_index].meta,
                "Too many missing numbers for currency group '{}'".format(currency),
                None,
            )
        )
        out_postings = []

    else:
        # If there is a single missing number, calculate it and fill it in here.
        missing, index = incomplete[0]
        incomplete_posting = postings[index]

        # Convert augmenting postings' costs from CostSpec to corresponding Cost
        # instances, except for the incomplete posting.
        new_postings = [
            (
                posting
                if posting is incomplete_posting
                else convert_costspec_to_cost(posting)
            )
            for posting in postings
        ]

        # Compute the balance of the other postings.
        residual = interpolate.compute_residual(
            posting for posting in new_postings if posting is not incomplete_posting
        )
        assert len(residual) < 2, "Internal error in grouping postings by currencies."
        if not residual.is_empty():
            respos = next(iter(residual))
            assert respos.cost is None, (
                "Internal error; cost appears in weight calculation."
            )
            assert respos.units.currency == currency, (
                "Internal error; residual different than currency group."
            )
            weight = -respos.units.number
            weight_currency = respos.units.currency
        else:
            weight = ZERO
            weight_currency = currency

        if missing == MissingType.UNITS:
            units = incomplete_posting.units
            cost = incomplete_posting.cost
            if cost:
                # Handle the special case where we only have total cost.
                if cost.number_per == ZERO:
                    errors.append(
                        InterpolationError(
                            incomplete_posting.meta,
                            "Cannot infer per-unit cost only from total",
                            None,
                        )
                    )
                    return postings, errors, True

                assert cost.currency == weight_currency, (
                    "Internal error; residual currency different than missing currency."
                )
                cost_total = cost.number_total or ZERO
                units_number = (weight - cost_total) / cost.number_per

            elif incomplete_posting.price:
                assert incomplete_posting.price.currency == weight_currency, (
                    "Internal error; residual currency different than missing currency."
                )
                units_number = weight / incomplete_posting.price.number

            else:
                assert units.currency == weight_currency, (
                    "Internal error; residual currency different than missing currency."
                )
                units_number = weight

            # Quantize the interpolated units if necessary.
            units_number = interpolate.quantize_with_tolerance(
                tolerances, units.currency, units_number
            )

            if weight != ZERO:
                new_pos = Position(Amount(units_number, units.currency), cost)
                new_posting = incomplete_posting._replace(
                    units=new_pos.units, cost=new_pos.cost
                )
            else:
                new_posting = None

        elif missing == MissingType.COST_PER:
            units = incomplete_posting.units
            cost = incomplete_posting.cost
            assert cost.currency == weight_currency, (
                "Internal error; residual currency different than missing currency."
            )
            if units.number != ZERO:
                number_per = (weight - (cost.number_total or ZERO)) / units.number
                new_cost = cost._replace(number_per=number_per)
                new_pos = Position(units, new_cost)
                new_posting = incomplete_posting._replace(
                    units=new_pos.units, cost=new_pos.cost
                )
            else:
                new_posting = None

        elif missing == MissingType.COST_TOTAL:
            units = incomplete_posting.units
            cost = incomplete_posting.cost
            assert cost.currency == weight_currency, (
                "Internal error; residual currency different than missing currency."
            )
            number_total = weight - cost.number_per * units.number
            new_cost = cost._replace(number_total=number_total)
            new_pos = Position(units, new_cost)
            new_posting = incomplete_posting._replace(
                units=new_pos.units, cost=new_pos.cost
            )

        elif missing == MissingType.PRICE:
            units = incomplete_posting.units
            cost = incomplete_posting.cost
            if cost is not None:
                errors.append(
                    InterpolationError(
                        incomplete_posting.meta,
                        "Cannot infer price for postings with units held at cost",
                        None,
                    )
                )
                return postings, errors, True
            else:
                price = incomplete_posting.price
                assert price.currency == weight_currency, (
                    "Internal error; residual currency different than missing currency."
                )
                new_price_number = abs(weight / units.number)
                new_posting = incomplete_posting._replace(
                    price=Amount(new_price_number, price.currency)
                )

        else:
            assert False, "Internal error; Invalid missing type."

        # Replace the number in the posting.
        if new_posting is not None:
            # Set meta-data on the new posting to indicate it was interpolated.
            if new_posting.meta is None:
                new_posting = new_posting._replace(meta={})
            new_posting.meta[interpolate.AUTOMATIC_META] = True

            # Convert augmenting posting costs from CostSpec to a corresponding
            # Cost instance.
            new_postings[index] = convert_costspec_to_cost(new_posting)
        else:
            del new_postings[index]
        out_postings = new_postings

    assert all(not isinstance(posting.cost, CostSpec) for posting in out_postings)

    # Check that units are non-zero and that no cost remains negative; issue an
    # error if this is the case.
    for posting in out_postings:
        if posting.cost is None:
            continue
        # If there is a cost, we don't allow either a cost value of zero,
        # nor a zero number of units. Note that we allow a price of zero as
        # the only special case allowed (for conversion entries), but never
        # for costs.
        if posting.units.number == ZERO:
            errors.append(
                InterpolationError(
                    posting.meta, 'Amount is zero: "{}"'.format(posting.units), None
                )
            )
        if posting.cost.number is not None and posting.cost.number < ZERO:
            errors.append(
                InterpolationError(
                    posting.meta, 'Cost is negative: "{}"'.format(posting.cost), None
                )
            )

    return out_postings, errors, (new_posting is not None)