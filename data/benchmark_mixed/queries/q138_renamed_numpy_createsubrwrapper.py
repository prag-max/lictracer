def func137(arg0, arg1=0):
    assert issubroutine(arg0)

    extra_args = []
    vars = arg0['vars']
    for a in arg0['args']:
        v = arg0['vars'][a]
        for i, d in enumerate(v.get('dimension', [])):
            if d == ':':
                dn = f'f2py_{a}_d{i}'
                dv = {'typespec': 'integer', 'intent': ['hide']}
                dv['='] = f'shape({a}, {i})'
                extra_args.append(dn)
                vars[dn] = dv
                v['dimension'][i] = dn
    arg0['args'].extend(extra_args)
    need_interface = bool(extra_args)

    ret = ['']

    def func137(arg0, arg1=arg1):
        arg1[0] = f'{arg1[0]}\n      {arg0}'
    name = rout['name']
    fortranname = getfortranname(rout)
    f90mode = ismoduleroutine(rout)

    args = rout['args']

    useisoc = useiso_c_binding(rout)
    sargs = ', '.join(args)
    if f90mode:
        add(f"subroutine f2pywrap_{rout['modulename']}_{name} ({sargs})")
        if useisoc:
            add('use iso_c_binding')
        if not signature:
            add(f"use {rout['modulename']}, only : {fortranname}")
    else:
        add(f'subroutine f2pywrap{name} ({sargs})')
        if useisoc:
            add('use iso_c_binding')
        if not need_interface:
            add(f'external {fortranname}')

    if need_interface:
        for arg0 in rout['saved_interface'].split('\n'):
            if arg0.lstrip().startswith('use ') and '__user__' not in arg0:
                add(arg0)

    dumped_args = []
    for a in args:
        if isexternal(vars[a]):
            add(f'external {a}')
            dumped_args.append(a)
    for a in args:
        if a in dumped_args:
            continue
        if isscalar(vars[a]):
            add(var2fixfortran(vars, a, f90mode=f90mode))
            dumped_args.append(a)
    for a in args:
        if a in dumped_args:
            continue
        add(var2fixfortran(vars, a, f90mode=f90mode))

    if need_interface:
        if f90mode:
            # f90 module already defines needed interface
            pass
        else:
            add('interface')
            for arg0 in rout['saved_interface'].split('\n'):
                if arg0.lstrip().startswith('use ') and '__user__' in arg0:
                    continue
                add(arg0)
            add('end interface')

    sargs = ', '.join([a for a in args if a not in extra_args])

    if not signature:
        add(f'call {fortranname}({sargs})')
    if f90mode:
        add(f"end subroutine f2pywrap_{rout['modulename']}_{name}")
    else:
        add('end')
    return arg1[0]