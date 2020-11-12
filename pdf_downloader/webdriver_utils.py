import platform
import os
from .exceptions import OperatingSystemIncompatible


def get_current_os():
    return platform.system()


def get_driver_path():
    current_os = get_current_os()
    working_directory = os.getcwd()
    if current_os == "Windows":
        return os.path.join(os.getcwd(), "drivers", "chromedriverWin32.exe")
    elif current_os == "Linux":
        return os.path.join(os.getcwd(), "drivers", "chromedriverLinux64")
    elif current_os == "Darwin":
        return os.path.join(os.getcwd(), "drivers", "chromedriverMac64")
    else:
        raise OperatingSystemIncompatible
