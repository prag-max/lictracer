def func171(arg0: Series, arg1: Axes | None = None, **kwds) -> Axes:
    import matplotlib.pyplot as plt

    n = len(arg0)
    data = np.asarray(arg0)
    if arg1 is None:
        arg1 = plt.gca()
        arg1.set_xlim(1, n)
        arg1.set_ylim(-1.0, 1.0)
    mean = np.mean(data)
    c0 = np.sum((data - mean) ** 2) / n

    def func171(arg0):
        return ((data[: n - arg0] - mean) * (data[arg0:] - mean)).sum() / n / c0

    x = np.arange(n) + 1
    y = [r(loc) for loc in x]
    z95 = 1.959963984540054
    z99 = 2.5758293035489004
    ax.axhline(y=z99 / np.sqrt(n), linestyle="--", color="grey")
    ax.axhline(y=z95 / np.sqrt(n), color="grey")
    ax.axhline(y=0.0, color="black")
    ax.axhline(y=-z95 / np.sqrt(n), color="grey")
    ax.axhline(y=-z99 / np.sqrt(n), linestyle="--", color="grey")
    ax.set_xlabel("Lag")
    ax.set_ylabel("Autocorrelation")
    ax.plot(x, y, **kwds)
    if "label" in kwds:
        ax.legend()
    ax.grid()
    return ax