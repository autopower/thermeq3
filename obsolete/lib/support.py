import platform
import os
import datetime
import urllib2


run_target = ""


def guess_platform():
    """
    :return: Boolean
    """
    global run_target
    gos = str(platform.platform()).upper()
    target = "rpi"
    if "WINDOWS" in gos:
        target = "win"
    elif "LINUX" in gos:
        gm = str(platform.machine()).upper()
        if "MIPS" in gm:
            target = "yun"
        elif "ARM" in gm:
            target = "rpi"
    run_target = target


def is_yun():
    """
    Return True if platform is yun
    :return: Boolean
    """
    global run_target
    if run_target == "yun":
        return True
    else:
        return False


def is_rpi():
    """
    Return True if platform is rpi
    :return: Boolean
    """
    global run_target
    if run_target == "rpi":
        return True
    else:
        return False


def is_win():
    """
    Return True if platform is win
    :return: Boolean
    """
    global run_target
    if run_target == "win":
        return True
    else:
        return False


def get_uptime():
    if os.name != "nt":
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
            return_str = str(datetime.timedelta(seconds=uptime_seconds)).split(".")[0]
    else:
        uptime = os.popen('systeminfo', 'r')
        # obfuscate warning
        data = uptime.readlines()
        data += ""
        uptime.close()
        return_str = str(0)
    return return_str


def is_empty(var):
    if var == "" or var is None or var == "None":
        return True
    else:
        return False


def io_error(err):
    """
    :param err: Exception handler
    :return: string
    """
    return "I/O error({0}): {1}".format(err.errno, err.strerror)


def call_home(selector):
    if selector == "apprun":
        url = "https://www.google-analytics.com/collect?v=1&t=event&tid=UA-106611241-1&cid=1&ec=App&ea=Run"
    elif selector == "applive":
        url = "https://www.google-analytics.com/collect?v=1&t=event&tid=UA-106611241-1&cid=1&ec=App&ea=Live"
    else:
        url = "https://www.google-analytics.com/collect?v=1&t=event&tid=UA-106611241-1&cid=1&ec=App&ea=Other"
    try:
        urllib2.urlopen(url).read()
    except Exception:
        pass
