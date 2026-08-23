def createfuncwrapper(rout, signature=0):
    assert isfunction(rout)

    vars = rout['vars']
    for a in rout['args']:
        v = rout['vars'][a]
        for i, d in enumerate(v.get('dimension', [])):
            if d == ':':
                dn = f'f2py_{a}_d{i}'
                dv = {'typespec': 'integer', 'intent': ['hide']}
                dv['='] = f'shape({a}, {i})'
                extra_args.append(dn)
                vars[dn] = dv
                v['dimension'][i] = dn
    rout['args'].extend(extra_args)
    need_interface = bool(extra_args)

    ret = ['']

    def add(line, ret=ret):
        ret[0] = f'{ret[0]}\n      {line}'
    name = rout['name']
    fortranname = getfortranname(rout)
    f90mode = ismoduleroutine(rout)
    newname = f'{name}f2pywrap'

    if newname not in vars:
        vars[newname] = vars[name]
        args = [newname] + rout['args'][1:]
    else:
        args = [newname] + rout['args']

    l_tmpl = var2fixfortran(vars, name, '@@@NAME@@@', f90mode)
    if l_tmpl[:13] == 'character*(*)':
        if f90mode:
            l_tmpl = 'character(len=10)' + l_tmpl[13:]
        else:
            l_tmpl = 'character*10' + l_tmpl[13:]
        charselect = vars[name]['charselector']
        if charselect.get('*', '') == '(*)':
            charselect['*'] = '10'

    l1 = l_tmpl.replace('@@@NAME@@@', newname)
    rl = None

    useisoc = useiso_c_binding(rout)
    sargs = ', '.join(args)
    if f90mode:
        # gh-23598 fix warning
        # Essentially, this gets called again with modules where the name of the
        # function is added to the arguments, which is not required, and removed
        sargs = sargs.replace(f"{name}, ", '')
        args = [arg for arg in args if arg != name]
        rout['args'] = args
        add(f"subroutine f2pywrap_{rout['modulename']}_{name} ({sargs})")
        if not signature:
            add(f"use {rout['modulename']}, only : {fortranname}")
        if useisoc:
            add('use iso_c_binding')
    else:
        add(f'subroutine f2pywrap{name} ({sargs})')
        if useisoc:
            add('use iso_c_binding')
        if not need_interface:
            add(f'external {fortranname}')
            rl = l_tmpl.replace('@@@NAME@@@', '') + ' ' + fortranname

    if need_interface:
        for line in rout['saved_interface'].split('\n'):
            if line.lstrip().startswith('use ') and '__user__' not in line:
                add(line)

    args = args[1:]
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
        if isintent_in(vars[a]):
            add(var2fixfortran(vars, a, f90mode=f90mode))
            dumped_args.append(a)
    for a in args:
        if a in dumped_args:
            continue
        add(var2fixfortran(vars, a, f90mode=f90mode))

    add(l1)
    if rl is not None:
        add(rl)

    if need_interface:
        if f90mode:
            # f90 module already defines needed interface
            pass
        else:
            add('interface')
            add(rout['saved_interface'].lstrip())
            add('end interface')

    sargs = ', '.join([a for a in args if a not in extra_args])

    if not signature:
        if islogicalfunction(rout):
            add(f'{newname} = .not.(.not.{fortranname}({sargs}))')
        else:
            add(f'{newname} = {fortranname}({sargs})')
    if f90mode:
        add(f"end subroutine f2pywrap_{rout['modulename']}_{name}")
    else:
        add('end')
    return ret[0]