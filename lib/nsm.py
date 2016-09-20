#!/usr/bin/env python
import thermeq3
import mailer
import sys
import time
import os


def redirect_error(on_off):
    """
    Turn error redirection on or off
    :param on_off: boolean
    :return: nothing
    """
    if on_off:
        t3.setup.stderr_log = t3.setup.place + t3.setup.devname + "_error.log"
        try:
            t3.var.ferr = open(t3.setup.stderr_log, "a")
        except Exception:
            raise
        else:
            t3.var.original_stderr = sys.stderr
            sys.stderr = t3.var.ferr
            # print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection active"
    else:
        # print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection closed"
        sys.stderr = t3.var.original_stderr
        t3.var.ferr.close()


if __name__ == '__main__':
    t3 = thermeq3.Thermeq3Object()
    if not t3.err_str == "":
        print t3.err_str
        exit()

    t3.prepare()

    if mailer.send_error_log(t3.setup, t3.setup.stderr_log):
        os.remove(t3.setup.stderr_log)

    redirect_error(True)

    while 1:
        if t3.intervals() == 0xFF:
            break
        time.sleep(t3.setup.intervals["slp"][0])

    redirect_error(False)
