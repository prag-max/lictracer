def func212(arg0, arg1):
    """
    name,begintitle,endtitle,argname
    ctype,rctype,maxnofargs,nofoptargs,returncptr
    """
    ret = {'name': f"cb_{arg0['name']}_in_{arg1}",
           'returncptr': ''}
    if isintent_callback(arg0):
        if '_' in arg0['name']:
            F_FUNC = 'F_FUNC_US'
        else:
            F_FUNC = 'F_FUNC'
        ret['callbackname'] = f"{F_FUNC}({arg0['name'].lower()},{arg0['name'].upper()})"
        ret['static'] = 'extern'
    else:
        ret['callbackname'] = ret['name']
        ret['static'] = 'static'
    ret['argname'] = arg0['name']
    ret['begintitle'] = gentitle(ret['name'])
    ret['endtitle'] = gentitle(f"end of {ret['name']}")
    ret['ctype'] = getctype(arg0)
    ret['rctype'] = 'void'
    if ret['ctype'] == 'string':
        ret['rctype'] = 'void'
    else:
        ret['rctype'] = ret['ctype']
    if ret['rctype'] != 'void':
        if iscomplexfunction(arg0):
            ret['returncptr'] = """
#ifdef F2PY_CB_RETURNCOMPLEX
return_value=
#endif
"""
        else:
            ret['returncptr'] = 'return_value='
    if ret['ctype'] in cformat_map:
        ret['showvalueformat'] = f"{cformat_map[ret['ctype']]}"
    if isstringfunction(arg0):
        ret['strlength'] = getstrlength(arg0)
    if isfunction(arg0):
        if 'result' in arg0:
            a = arg0['result']
        else:
            a = arg0['name']
        if hasnote(arg0['vars'][a]):
            ret['note'] = arg0['vars'][a]['note']
            arg0['vars'][a]['note'] = ['See elsewhere.']
        ret['rname'] = a
        ret['pydocsign'], ret['pydocsignout'] = getpydocsign(a, arg0)
        if iscomplexfunction(arg0):
            ret['rctype'] = """
#ifdef F2PY_CB_RETURNCOMPLEX
#ctype#
#else
void
#endif
"""
    elif hasnote(arg0):
        ret['note'] = arg0['note']
        arg0['note'] = ['See elsewhere.']
    nofargs = 0
    nofoptargs = 0
    if 'args' in arg0 and 'vars' in arg0:
        for a in arg0['args']:
            var = arg0['vars'][a]
            if l_or(isintent_in, isintent_inout)(var):
                nofargs = nofargs + 1
                if isoptional(var):
                    nofoptargs = nofoptargs + 1
    ret['maxnofargs'] = repr(nofargs)
    ret['nofoptargs'] = repr(nofoptargs)
    if hasnote(arg0) and isfunction(arg0) and 'result' in arg0:
        ret['routnote'] = arg0['note']
        arg0['note'] = ['See elsewhere.']
    return ret