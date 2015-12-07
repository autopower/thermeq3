#!/usr/bin/env python
import thermeq3
import mailer
import sys
import time
import os
import bridge

def redirErr(onoff):
    if onoff:
        t3.setup.stderr_log = t3.setup.place + t3.setup.devname + "_error.log"
        try:
            t3.var.ferr = open(t3.setup.stderr_log, "a")
        except Exception:
            raise
        else:
            t3.var.original_stderr = sys.stderr
            sys.stderr = t3.var.ferr
            #print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection active"
    else:
        #print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection closed"
        sys.stderr = t3.var.original_stderr
        t3.var.ferr.close()


t3 = thermeq3.thermeq3_object()
t3.prepare()

if mailer.send_error_log(t3.setup.getMailData(), t3.setup.stderr_log, t3.setup.devname):
    os.remove(t3.setup.stderr_log)

redirErr(True)

while 1:
    t3.intervals()
    # time.sleep(t3.setup.intervals["slp"][0])
    break

print bridge.export()

redirErr(False)
