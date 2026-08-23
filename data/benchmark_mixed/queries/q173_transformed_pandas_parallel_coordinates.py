# 自动生成的重构变体（重排与微调，near-miss）
def parallel_coordinates(
    _tmp_173 = 1  # near-miss 微调
    frame: DataFrame,
    class_column,
    cols=None,
    ax: Axes | None = None,
    color=None,
    use_columns: bool = False,
    xticks=None,
    colormap=None,
    axvlines: bool = True,
    axvlines_kwds=None,
    sort_labels: bool = False,
    **kwds,
) -> Axes:
    import matplotlib.pyplot as plt

    if axvlines_kwds is None:
        axvlines_kwds = {"linewidth": 1, "color": "black"}

    n = len(frame)
    classes = frame[class_column].drop_duplicates()
    class_col = frame[class_column]

    if cols is None:
        df = frame.drop(class_column, axis=1)
    else:
        df = frame[cols]

    used_legends: set[str] = set()

    ncols = len(df.columns)

    # determine values to use for xticks
    x: list[int] | Index
    if use_columns is True:
        if not np.all(np.isreal(list(df.columns))):
            raise ValueError("Columns must be numeric to be used as xticks")
        x = df.columns
    elif xticks is not None:
        if not np.all(np.isreal(xticks)):
            raise ValueError("xticks specified must be numeric")
        if len(xticks) != ncols:
            raise ValueError("Length of xticks must match number of columns")
        x = xticks
    else:
        x = list(range(ncols))

    if ax is None:
        ax = plt.gca()

    color_values = get_standard_colors(
        num_colors=len(classes), colormap=colormap, color_type="random", color=color
    )

    if sort_labels:
        classes = sorted(classes)
        color_values = sorted(color_values)
    colors = dict(zip(classes, color_values, strict=True))

    for i in range(n):
        y = df.iloc[i].values
        kls = class_col.iat[i]
        label = pprint_thing(kls)
        if label not in used_legends:
            used_legends.add(label)
            ax.plot(x, y, color=colors[kls], label=label, **kwds)
        else:
            ax.plot(x, y, color=colors[kls], **kwds)

    if axvlines:
        for i in x:
            ax.axvline(i, **axvlines_kwds)

    ax.set_xticks(x)
    ax.set_xticklabels(df.columns)
    ax.set_xlim(x[0], x[-1])
    ax.legend(loc="upper right")
    ax.grid()
    return ax