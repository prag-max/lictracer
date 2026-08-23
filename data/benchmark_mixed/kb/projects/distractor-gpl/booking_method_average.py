def booking_method_AVERAGE(entry, posting, matches):
    """AVERAGE booking method implementation.

    Args:
      entry: The parent Transaction instance.
      posting: An instance of Posting, the reducing posting which we're
        attempting to match.
      matches: A list of matching Position instances from the ante-inventory.
    Returns:
      A tuple of (booked_reductions, booked_matches, errors, insufficient).
    """
    booked_reductions = []
    booked_matches = []
    errors = [AmbiguousMatchError(entry.meta, "AVERAGE method is not supported", entry)]
    return booked_reductions, booked_matches, errors, False

    # FIXME: Future implementation here.

    if False:
        # DISABLED - This is the code for AVERAGE, which is currently disabled.

        # If there is more than a single match we need to ultimately merge the
        # postings. Also, if the reducing posting provides a specific cost, we
        # need to update the cost basis as well. Both of these cases are carried
        # out by removing all the matches and readding them later on.
        if len(matches) == 1 and (
            not isinstance(posting.cost.number_per, Decimal)
            and not isinstance(posting.cost.number_total, Decimal)
        ):
            # There is no cost. Just reduce the one leg. This should be the
            # normal case if we always merge augmentations and the user lets
            # Beancount deal with the cost.
            match = matches[0]
            sign = -1 if posting.units.number < ZERO else 1
            number = min(abs(match.units.number), abs(posting.units.number))
            match_units = Amount(number * sign, match.units.currency)
            booked_reductions.append(posting._replace(units=match_units, cost=match.cost))
            _insufficient = match_units.number != posting.units.number
        else:
            # Merge the matching postings to a single one.
            merged_units = inventory.Inventory()
            merged_cost = inventory.Inventory()
            for match in matches:
                merged_units.add_amount(match.units)
                merged_cost.add_amount(convert.get_weight(match))
            if len(merged_units) != 1 or len(merged_cost) != 1:
                errors.append(
                    AmbiguousMatchError(
                        entry.meta,
                        "Cannot merge positions in multiple currencies: {}".format(
                            ", ".join(
                                position.to_string(match_posting)
                                for match_posting in matches
                            )
                        ),
                        entry,
                    )
                )
            else:
                if isinstance(posting.cost.number_per, Decimal) or isinstance(
                    posting.cost.number_total, Decimal
                ):
                    errors.append(
                        AmbiguousMatchError(
                            entry.meta,
                            "Explicit cost reductions aren't supported yet: {}".format(
                                position.to_string(posting)
                            ),
                            entry,
                        )
                    )
                else:
                    # Insert postings to remove all the matches.
                    booked_reductions.extend(
                        posting._replace(
                            units=-match.units, cost=match.cost, flag=flags.FLAG_MERGING
                        )
                        for match in matches
                    )
                    units = merged_units[0].units
                    date = matches[0].cost.date  ## FIXME: Select which one,
                    ## oldest or latest.
                    cost_units = merged_cost[0].units
                    cost = Cost(
                        cost_units.number / units.number, cost_units.currency, date, None
                    )

                    # Insert a posting to refill those with a replacement match.
                    booked_reductions.append(
                        posting._replace(units=units, cost=cost, flag=flags.FLAG_MERGING)
                    )

                    # Now, match the reducing request against this lot.
                    booked_reductions.append(
                        posting._replace(units=posting.units, cost=cost)
                    )
                    _insufficient = abs(posting.units.number) > abs(units.number)