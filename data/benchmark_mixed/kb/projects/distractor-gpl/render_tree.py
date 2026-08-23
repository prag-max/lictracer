def render_tree(root):
    """Render a tree of nodes.

    Returns:
      A list of tuples of (first_line, continuation_line, node) where
        first_line: A string, the first line to render, which includes the
          account name.
        continuation_line: A string, further line to render if necessary.
        node: The Node instance which corresponds to this line.
      and an integer, the width of the new columns.
    """
    # Compute all the lines ahead of time in order to calculate the width.
    lines = []

    # Start with the root node. We push the constant prefix before this node,
    # the account name, and the RealAccount instance. We will maintain a stack
    # of children nodes to render.
    stack = [("", root.name, root, True)]
    while stack:
        prefix, name, node, is_last = stack.pop(-1)

        if node is root:
            # For the root node, we don't want to render any prefix.
            first = cont = ""
        else:
            # Compute the string that precedes the name directly and the one below
            # that for the continuation lines.
            #  |
            #  @@@ Bank1    <----------------
            #  @@@ |
            #  |   |-- Checking
            if is_last:
                first = prefix + PREFIX_LEAF_1
                cont = prefix + PREFIX_LEAF_C
            else:
                first = prefix + PREFIX_CHILD_1
                cont = prefix + PREFIX_CHILD_C

        # Compute the name to render for continuation lines.
        #  |
        #  |-- Bank1
        #  |   @@@       <----------------
        #  |   |-- Checking
        if len(node) > 0:
            cont_name = PREFIX_CHILD_C
        else:
            cont_name = PREFIX_LEAF_C

        # Add a line for this account.
        if not (node is root and not name):
            lines.append((first + name, cont + cont_name, node))

        # Push the children onto the stack, being careful with ordering and
        # marking the last node as such.
        if node:
            child_items = reversed(node)
            child_iter = iter(child_items)
            child_node = next(child_iter)
            stack.append((cont, child_node.name, child_node, True))
            for child_node in child_iter:
                stack.append((cont, child_node.name, child_node, False))

    if not lines:
        return lines

    # Compute the maximum width of the lines and convert all of them to the same
    # maximal width. This makes it easy on the client.
    max_width = max(len(first_line) for first_line, _, __ in lines)
    line_format = "{{:{width}}}".format(width=max_width)
    return [
        (line_format.format(first_line), line_format.format(cont_line), node)
        for (first_line, cont_line, node) in lines
    ], max_width