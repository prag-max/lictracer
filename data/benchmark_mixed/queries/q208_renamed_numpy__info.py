def func207(arg0, arg1=None):
    """Provide information about ndarray arg0.

    Parameters
    ----------
    arg0 : ndarray
        Must be ndarray, not checked.
    arg1
        Where printed arg1 goes.

    Notes
    -----
    Copied over from the numarray module prior to its removal.
    Adapted somewhat as only numpy is an option now.

    Called by info.

    """
    extra = ""
    tic = ""
    bp = lambda x: x
    cls = getattr(arg0, '__class__', type(arg0))
    nm = getattr(cls, '__name__', cls)
    strides = arg0.strides
    endian = arg0.dtype.byteorder

    if arg1 is None:
        arg1 = sys.stdout

    print("class: ", nm, file=arg1)
    print("shape: ", arg0.shape, file=arg1)
    print("strides: ", strides, file=arg1)
    print("itemsize: ", arg0.itemsize, file=arg1)
    print("aligned: ", bp(arg0.flags.aligned), file=arg1)
    print("contiguous: ", bp(arg0.flags.contiguous), file=arg1)
    print("fortran: ", arg0.flags.fortran, file=arg1)
    print(
        f"data pointer: {hex(arg0.ctypes._as_parameter_.value)}{extra}",
        file=arg1
        )
    print("byteorder: ", end=' ', file=arg1)
    if endian in ['|', '=']:
        print(f"{tic}{sys.byteorder}{tic}", file=arg1)
        byteswap = False
    elif endian == '>':
        print(f"{tic}big{tic}", file=arg1)
        byteswap = sys.byteorder != "big"
    else:
        print(f"{tic}little{tic}", file=arg1)
        byteswap = sys.byteorder != "little"
    print("byteswap: ", bp(byteswap), file=arg1)
    print(f"type: {arg0.dtype}", file=arg1)