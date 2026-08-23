def book_reductions(entry, group_postings, balances, methods):
    """Book inventory reductions against the ante-balances.

    This function accepts a dict of (account, Inventory balance) and for each
    posting that is a reduction against its inventory, attempts to find a
    corresponding lot or list of lots to reduce the balance with.

    * For reducing lots, the CostSpec instance of the posting is replaced by a
      Cost instance.

    * For augmenting lots, the CostSpec instance of the posting is left alone,
      except for its date, which is inherited from the parent Transaction.

    Args:
      entry: An instance of Transaction. This is only used to refer to when
        logging errors.
      group_postings: A list of Posting instances for the group.
      balances: A dict of account name to inventory contents.
      methods: A mapping of account name to their corresponding booking
        method enum.
    Returns:
      A pair of
        booked_postings: A list of booked postings, with reducing lots resolved
          against specific position in the corresponding accounts'
          ante-inventory balances. Note single reducing posting in the input may
          result in multiple postings in the output. Also note that augmenting
          postings held-at-cost will still refer to 'cost' instances of
          CostSpec, left to be interpolated later.
        errors: A list of errors, if there were any.
    """
    errors = []

    # A local copy of the balances dictionary which is updated just for the
    # duration of this function's updates, in order to take into account the
    # cumulative effect of all the postings inferred here
    local_balances = {}

    empty = inventory.Inventory()
    booked_postings = []
    for posting in group_postings:
        # Process a single posting.
        units = posting.units
        costspec = posting.cost
        account = posting.account

        # Note: We ensure there is no mutation on 'balances' to keep this
        # function without side-effects. Note that we may be able to optimize
        # performance later on by giving up this property.
        #
        # Also note that if there is no existing balance, then won't be any lot
        # reduction because none of the postings will be able to match against
        # any currencies of the balance.
        if account not in local_balances:
            previous_balance = balances.get(account, empty)
            local_balances[account] = copy.copy(previous_balance)
        balance = local_balances[account]

        # Check if this is a lot held at cost.
        if costspec is None or units.number is MISSING:
            # This posting is not held at cost; we do nothing.
            booked_postings.append(posting)
        else:
            # This posting is held at cost; figure out if it's a reduction or an
            # augmentation.
            method = methods[account]
            if (
                method is not Booking.NONE
                and balance is not None
                and balance.is_reduced_by(units)
            ):
                # This posting is a reduction.

                # Match the positions.
                cost_number = compute_cost_number(costspec, units)
                matches = []
                for position in balance:
                    # Skip inventory contents of a different currency.
                    if units.currency and position.units.currency != units.currency:
                        continue
                    # Skip balance positions not held at cost.
                    if position.cost is None:
                        continue
                    if cost_number is not None and position.cost.number != cost_number:
                        continue
                    if (
                        isinstance(costspec.currency, str)
                        and position.cost.currency != costspec.currency
                    ):
                        continue
                    if costspec.date and position.cost.date != costspec.date:
                        continue
                    if costspec.label and position.cost.label != costspec.label:
                        continue
                    matches.append(position)

                # Check for ambiguous matches.
                if len(matches) == 0:
                    errors.append(
                        ReductionError(
                            entry.meta,
                            'No position matches "{}" against balance {}'.format(
                                posting, balance
                            ),
                            entry,
                        )
                    )
                    return [], errors  # This is irreconcilable, remove these postings.

                # TODO(blais): We'll have to change this, as we want to allow
                # positions crossing from negative to positive and vice-versa in
                # a simple application. See {d3cbd78f1029}.
                reduction_postings, matched_postings, ambi_errors = (
                    booking_method.handle_ambiguous_matches(entry, posting, matches, method)
                )
                if ambi_errors:
                    errors.extend(ambi_errors)
                    return [], errors

                # Add the reductions to the resulting list of booked postings.
                booked_postings.extend(reduction_postings)

                # Update the local balance in order to avoid matching against
                # the same postings twice when processing multiple postings in
                # the same transaction. Note that we only do this for postings
                # held at cost because the other postings may need interpolation
                # in order to be resolved properly.
                for posting in reduction_postings:
                    balance.add_position(posting)
            else:
                # This posting is an augmentation.
                #
                # Note that we do not convert the CostSpec instances to Cost
                # instances, because we want to let the subsequent interpolation
                # process able to interpolate either the cost per-unit or the
                # total cost, separately.

                # Put in the date of the parent Transaction if there is no
                # explicit date specified on the spec.
                if costspec.date is None:
                    dated_costspec = costspec._replace(date=entry.date)
                    posting = posting._replace(cost=dated_costspec)

                # FIXME: Insert unique ids for trade tracking; right now this
                # creates ambiguous matches errors (and it shouldn't).
                # # Insert a unique label if there isn't one.
                # if posting.cost is not None and posting.cost.label is None:
                #     posting = posting._replace(
                #         cost=posting.cost._replace(label=unique_label()))

                booked_postings.append(posting)

    return booked_postings, errors