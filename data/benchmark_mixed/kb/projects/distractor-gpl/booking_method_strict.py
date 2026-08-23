def booking_method_STRICT(entry, posting, matches):
    """Strict booking method. This method fails if there are ambiguous matches.

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
    errors = []
    insufficient = False

    # In strict mode, we require at most a single matching posting.
    if len(matches) > 1:
        # If the total requested to reduce matches the sum of all the
        # ambiguous postings, match against all of them.
        sum_matches = sum(p.units.number for p in matches)
        if sum_matches == -posting.units.number:
            booked_reductions.extend(
                posting._replace(units=-match.units, cost=match.cost) for match in matches
            )
        else:
            errors.append(
                AmbiguousMatchError(
                    entry.meta,
                    'Ambiguous matches for "{}": {}'.format(
                        position.to_string(posting),
                        ", ".join(
                            position.to_string(match_posting) for match_posting in matches
                        ),
                    ),
                    entry,
                )
            )
    else:
        # Replace the posting's units and cost values.
        match = matches[0]
        sign = -1 if posting.units.number < ZERO else 1
        number = min(abs(match.units.number), abs(posting.units.number))
        match_units = Amount(number * sign, match.units.currency)
        booked_reductions.append(posting._replace(units=match_units, cost=match.cost))
        booked_matches.append(match)
        insufficient = match_units.number != posting.units.number

    return booked_reductions, booked_matches, errors, insufficient