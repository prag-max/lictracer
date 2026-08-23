def get_windows_version():
    import ctypes


    os_version = OSVERSIONINFOEXW()
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    if retcode != 0:
        raise OSError

    return (
        os_version.dwMajorVersion,
        os_version.dwMinorVersion,
        os_version.dwBuildNumber,
    )