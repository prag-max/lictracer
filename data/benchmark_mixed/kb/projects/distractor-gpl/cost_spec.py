def cost_spec(self, filename, lineno, cost_comp_list, is_total):
        """Process a cost_spec grammar rule.

        Args:
          filename: The name of the file being processed.
          lineno: The current line number.
          cost_comp_list: A list of CompoundAmount, a datetime.date, or
            label ID strings.
          is_total: Assume only the total cost is specified; reject the <number> # <number>
              syntax, that is, no compound amounts may be specified. This is used to support
              the {{...}} syntax.
        Returns:
          A cost-info tuple of CompoundAmount, lot date and label string. Any of these
          may be set to a sentinel indicating "unset".
        """
        if not cost_comp_list:
            return CostSpec(MISSING, None, MISSING, None, None, False)
        assert isinstance(cost_comp_list, list), "Internal error in parser: {}".format(
            cost_comp_list
        )

        compound_cost = None
        date_ = None
        label = None
        merge = None
        for comp in cost_comp_list:
            if isinstance(comp, CompoundAmount):
                if compound_cost is None:
                    compound_cost = comp
                else:
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            "Duplicate cost: '{}'.".format(comp),
                        )
                    )

            elif isinstance(comp, date):
                if date_ is None:
                    date_ = comp
                else:
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            "Duplicate date: '{}'.".format(comp),
                        )
                    )

            elif comp is MERGE_COST:
                if merge is None:
                    merge = True
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            "Cost merging is not supported yet",
                        )
                    )
                else:
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            "Duplicate merge-cost spec",
                        )
                    )

            else:
                assert isinstance(comp, str), (
                    "Currency component is not string: '{}'".format(comp)
                )
                if label is None:
                    label = comp
                else:
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            "Duplicate label: '{}'.".format(comp),
                            None,
                        )
                    )

        # If there was a cost_comp_list, thus a "{...}" cost basis spec, you must
        # indicate that by creating a CompoundAmount(), always.

        if compound_cost is None:
            number_per, number_total, currency = MISSING, None, MISSING
        else:
            number_per, number_total, currency = compound_cost
            if is_total:
                if number_total is not None:
                    self.errors.append(
                        ParserError(
                            new_metadata(filename, lineno),
                            (
                                "Per-unit cost may not be specified using total cost "
                                "syntax: '{}'; ignoring per-unit cost"
                            ).format(compound_cost),
                        )
                    )
                    # Ignore per-unit number.
                    number_per = ZERO
                else:
                    # There's a single number specified; interpret it as a total cost.
                    number_total = number_per
                    number_per = ZERO

        if merge is None:
            merge = False

        return CostSpec(number_per, number_total, currency, date_, label, merge)