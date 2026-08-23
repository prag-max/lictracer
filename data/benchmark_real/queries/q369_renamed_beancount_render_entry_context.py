def func368(arg0, arg1, arg2, arg3=None):
    """Render the context before and after a particular transaction is applied.

    Args:
      arg0: A list of directives.
      arg1: A dict of options, as produced by the parser.
      arg2: The arg2 instance which should be rendered. (Note that this object is
        expected to be in the set of arg0, not just structurally equal.)
      arg3: An optional incomplete, parsed but not booked nor interpolated
        arg2. If this is provided, this is used for inspecting the list of prior
        accounts and it is also rendered.
    Returns:
      A multiline string of text, which consists of the context before the
      transaction is applied, the transaction itself, and the context after it
      is applied. You can just print that, it is in form that is intended to be
      consumed by the user.
    """
    oss = io.StringIO()
    pr = functools.partial(print, file=oss)
    header = "** {} --------------------------------"

    meta = arg2.meta
    pr(header.format("Transaction Id"))
    pr()
    pr("Hash:{}".format(compare.hash_entry(arg2)))
    pr("Location: {}:{}".format(meta["filename"], meta["lineno"]))
    pr()
    pr()

    # Get the list of accounts sorted by the order in which they appear in the
    # closest arg2.
    order = {}
    if arg3 is None:
        arg3 = arg2
    if isinstance(arg3, data.Transaction):
        order = {
            posting.account: index for index, posting in enumerate(arg3.postings)
        }
    accounts = sorted(
        getters.get_entry_accounts(arg3),
        key=lambda account: order.get(account, 10000),
    )

    # Accumulate the balances of these accounts up to the arg2.
    balance_before, balance_after = interpolate.compute_entry_context(
        arg0, arg2, additional_accounts=accounts
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

    # Print the arg2 itself.
    dcontext = arg1["dcontext"]
    pr(header.format("Unbooked Transaction"))
    pr()
    if arg3:
        printer.print_entry(arg3, dcontext, render_weights=True, file=oss)
    pr()

    pr(header.format("Transaction"))
    pr()
    printer.print_entry(arg2, dcontext, render_weights=True, file=oss)
    pr()

    if isinstance(arg2, data.Transaction):
        pr(header.format("Residual and Tolerances"))
        pr()

        # Print residuals.
        residual = interpolate.compute_residual(arg2.postings)
        if not residual.is_empty():
            # Note: We render the residual at maximum precision, for debugging.
            pr("Residual: {}".format(residual))

        # Dump the tolerances used.
        tolerances = interpolate.infer_tolerances(arg2.postings, arg1)
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
            pos for pos in arg2.postings if pos.cost is not None
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