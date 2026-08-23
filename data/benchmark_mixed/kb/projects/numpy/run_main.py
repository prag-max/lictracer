def run_main(comline_list):
    """
    Equivalent to running::

        f2py <args>

    where ``<args>=string.join(<list>,' ')``, but in Python.  Unless
    ``-h`` is used, this function returns a dictionary containing
    information on generated modules and their dependencies on source
    files.

    You cannot build extension modules with this function, that is,
    using ``-c`` is not allowed. Use the ``compile`` command instead.

    Examples
    --------
    The command ``f2py -m scalar scalar.f`` can be executed from Python as
    follows.

    .. literalinclude:: ../../source/f2py/code/results/run_main_session.dat
        :language: python

    """
    crackfortran.reset_global_f2py_vars()
    f2pydir = os.path.dirname(os.path.abspath(cfuncs.__file__))
    fobjhsrc = os.path.join(f2pydir, 'src', 'fortranobject.h')
    fobjcsrc = os.path.join(f2pydir, 'src', 'fortranobject.c')
    # gh-22819 -- begin
    parser = make_f2py_compile_parser()
    args, comline_list = parser.parse_known_args(comline_list)
    pyf_files, _ = filter_files("", "[.]pyf([.]src|)", comline_list)
    # Checks that no existing modulename is defined in a pyf file
    # TODO: Remove all this when scaninputline is replaced
    if args.module_name:
        if "-h" in comline_list:
            modname = (
                args.module_name
            )  # Directly use from args when -h is present
        else:
            modname = validate_modulename(
                pyf_files, args.module_name
            )  # Validate modname when -h is not present
        comline_list += ['-m', modname]  # needed for the rest of scaninputline
    # gh-22819 -- end
    files, options = scaninputline(comline_list)
    auxfuncs.options = options
    capi_maps.load_f2cmap_file(options['f2cmap_file'])
    postlist = callcrackfortran(files, options)
    isusedby = {}
    for plist in postlist:
        if 'use' in plist:
            for u in plist['use'].keys():
                if u not in isusedby:
                    isusedby[u] = []
                isusedby[u].append(plist['name'])
    for plist in postlist:
        module_name = plist['name']
        if plist['block'] == 'python module' and '__user__' in module_name:
            if module_name in isusedby:
                # if not quiet:
                usedby = ','.join(f'"{s}"' for s in isusedby[module_name])
                outmess(
                    f'Skipping Makefile build for module "{module_name}" '
                    f'which is used by {usedby}\n')
    if 'signsfile' in options:
        if options['verbose'] > 1:
            outmess(
                'Stopping. Edit the signature file and then run f2py on the signature file: ')
            outmess(f"{os.path.basename(sys.argv[0])} {options['signsfile']}\n")
        return
    for plist in postlist:
        if plist['block'] != 'python module':
            if 'python module' not in options:
                errmess(
                    'Tip: If your original code is Fortran source then you must use -m option.\n')
            raise TypeError('All blocks must be python module blocks but got '
                            f'{plist["block"]!r}')
    auxfuncs.debugoptions = options['debug']
    f90mod_rules.options = options
    auxfuncs.wrapfuncs = options['wrapfuncs']

    ret = buildmodules(postlist)

    for mn in ret.keys():
        dict_append(ret[mn], {'csrc': fobjcsrc, 'h': fobjhsrc})
    return ret