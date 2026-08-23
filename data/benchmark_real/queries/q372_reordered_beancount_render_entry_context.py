def render_entry_context(entries, options_map, entry, parsed_entry=None):
    """Render the context before and after a particular transaction is applied.

    Args:
      entries: A list of directives.
      options_map: A dict of options, as produced by the parser.
      entry: The entry instance which should be rendered. (Note that this object is
        expected to be in the set of entries, not just structurally equal.)
      parsed_entry: An optional incomplete, parsed but not booked nor interpolated
        entry. If this is provided, this is used for inspecting the list of prior
        accounts and it is also rendered.
    Returns:
      A multiline string of text, which consists of the context before the
      transaction is applied, the transaction itself, and the context after it
      is applied. You can just print that, it is in form that is intended to be
      consumed by the user.
    """
    oss = io.StringIO()
    pr = functools.partial(print, file=oss)
    meta = entry.meta
    header = "** {} --------------------------------"
    pr(header.format("Transaction Id"))
    pr()
    pr("Hash:{}".format(compare.hash_entry(entry)))
    pr("Location: {}:{}".format(meta["filename"], meta["lineno"]))
    pr()
    pr()

    # Get the list of accounts sorted by the order in which they appear in the
    # closest entry.
    order = {}
    if parsed_entry is None:
        parsed_entry = entry
    if isinstance(parsed_entry, data.Transaction):
        order = {
            posting.account: index for index, posting in enumerate(parsed_entry.postings)
        }
    accounts = sorted(
        getters.get_entry_accounts(parsed_entry),
        key=lambda account: order.get(account, 10000),
    )

    # Accumulate the balances of these accounts up to the entry.
    balance_before, balance_after = interpolate.compute_entry_context(
        entries, entry, additional_accounts=accounts
    )

    # Create a format line for printing the contents of account balances.
    max_account_width = max(map(len, accounts)) if accounts else 1
    position_line = "{{:1}} {{:{width}}}  {{:>49}}".format(width=max_account_width)

    # Print the context before.
    pr(header.format("Balances before transaction"))
    pr()
    before_hashes = set()
    average_costs = {}
    for account in accounts:
        balance = balance_before[account]

        pc_balances = balance.split()
        for currency, pc_balance in pc_balances.items():
            if len(pc_balance) > 1:
                average_costs[account] = pc_balance.average()

        positions = balance.get_positions()
        for position in positions:
            before_hashes.add((account, hash(position)))
            pr(position_line.format("", account, str(position)))
        if not positions:
            pr(position_line.format("", account, ""))
        pr()
    pr()

    # Print average cost per account, if relevant.
    if average_costs:
        pr(header.format("Average Costs"))
        pr()
        for account, average_cost in sorted(average_costs.items()):
            for position in average_cost:
                pr(position_line.format("", account, str(position)))
        pr()
        pr()

    # Print the entry itself.
    dcontext = options_map["dcontext"]
    pr(header.format("Unbooked Transaction"))
    pr()
    if parsed_entry:
        printer.print_entry(parsed_entry, dcontext, render_weights=True, file=oss)
    pr()

    pr(header.format("Transaction"))
    pr()
    printer.print_entry(entry, dcontext, render_weights=True, file=oss)
    pr()

    if isinstance(entry, data.Transaction):
        pr(header.format("Residual and Tolerances"))
        pr()

        # Print residuals.
        residual = interpolate.compute_residual(entry.postings)
        if not residual.is_empty():
            # Note: We render the residual at maximum precision, for debugging.
            pr("Residual: {}".format(residual))

        # Dump the tolerances used.
        tolerances = interpolate.infer_tolerances(entry.postings, options_map)
        if tolerances:
            pr(
                "Tolerances: {}".format(
                    ", ".join(
                        "{}={}".format(key, value)
                        for key, value in sorted(tolerances.items())
                    )
                )
            )

        # Compute the total cost basis.
        cost_basis = inventory.Inventory(
            pos for pos in entry.postings if pos.cost is not None
        ).reduce(convert.get_cost)
        if not cost_basis.is_empty():
            pr("Basis: {}".format(cost_basis))
        pr()
        pr()

    # Print the context after.
    pr(header.format("Balances after transaction"))
    pr()
    for account in accounts:
        positions = balance_after[account].get_positions()
        for position in positions:
            changed = (account, hash(position)) not in before_hashes
            print(
                position_line.format("*" if changed else "", account, str(position)),
                file=oss,
            )
        if not positions:
            pr(position_line.format("", account, ""))
        pr()

    return oss.getvalue()