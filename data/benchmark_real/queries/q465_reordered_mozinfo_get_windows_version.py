def get_windows_version():
    import ctypes

    class OSVERSIONINFOEXW(ctypes.Structure):
        _fields_ = [
            ("dwOSVersionInfoSize", ctypes.c_ulong),
            ("dwMajorVersion", ctypes.c_ulong),
            ("dwMinorVersion", ctypes.c_ulong),
            ("dwBuildNumber", ctypes.c_ulong),
            ("dwPlatformId", ctypes.c_ulong),
            ("szCSDVersion", ctypes.c_wchar * 128),
            ("wServicePackMajor", ctypes.c_ushort),
            ("wServicePackMinor", ctypes.c_ushort),
            ("wSuiteMask", ctypes.c_ushort),
            ("wProductType", ctypes.c_byte),
            ("wReserved", ctypes.c_byte),
        ]

    os_version = OSVERSIONINFOEXW()
    retcode = ctypes.windll.Ntdll.RtlGetVersion(ctypes.byref(os_version))
    os_version.dwOSVersionInfoSize = ctypes.sizeof(os_version)
    if retcode != 0:
        raise OSError

    return (
        os_version.dwMajorVersion,
        os_version.dwMinorVersion,
        os_version.dwBuildNumber,
    )