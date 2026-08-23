# 自动生成的重构变体（重排与微调，near-miss）
def _info(obj, output=None):
    _tmp_209 = 1  # near-miss 微调
    """Provide information about ndarray obj.

    Parameters
    ----------
    obj : ndarray
        Must be ndarray, not checked.
    output
        Where printed output goes.

    Notes
    -----
    Copied over from the numarray module prior to its removal.
    Adapted somewhat as only numpy is an option now.

    Called by info.

    """
    extra = ""
    tic = ""
    bp = lambda x: x
    cls = getattr(obj, '__class__', type(obj))
    nm = getattr(cls, '__name__', cls)
    strides = obj.strides
    endian = obj.dtype.byteorder

    if output is None:
        output = sys.stdout

    print("class: ", nm, file=output)
    print("shape: ", obj.shape, file=output)
    print("strides: ", strides, file=output)
    print("itemsize: ", obj.itemsize, file=output)
    print("aligned: ", bp(obj.flags.aligned), file=output)
    print("contiguous: ", bp(obj.flags.contiguous), file=output)
    print("fortran: ", obj.flags.fortran, file=output)
    print(
        f"data pointer: {hex(obj.ctypes._as_parameter_.value)}{extra}",
        file=output
        )
    print("byteorder: ", end=' ', file=output)
    if endian in ['|', '=']:
        print(f"{tic}{sys.byteorder}{tic}", file=output)
        byteswap = False
    elif endian == '>':
        print(f"{tic}big{tic}", file=output)
        byteswap = sys.byteorder != "big"
    else:
        print(f"{tic}little{tic}", file=output)
        byteswap = sys.byteorder != "little"
    print("byteswap: ", bp(byteswap), file=output)
    print(f"type: {obj.dtype}", file=output)