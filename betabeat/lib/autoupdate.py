import urllib2
import traceback
import httplib
import logmsg
import os
import hashlib

upd_files = ["nsm", "thermeq3", "maxeq3", "secweb", "bridge", "mailer", "logmsg"]


def getHash(filename):
    checksum = hashlib.md5()
    if os.path.isfile(filename):
        f = file(filename, "rb")
        while True:
            part = f.read(1024)
            if not part:
                break
            checksum.update(part)
        f.close()
    return checksum


def downloadFile(homedir, base, filename):
    errstr = ""
    try:
        request = urllib2.urlopen(base + "/" + filename)
        response = request.read()
    except urllib2.HTTPError, e:
        errstr += "HTTPError = " + str(e.reason)
    except urllib2.URLError, e:
        errstr += "URLError = " + str(e.reason)
    except httplib.HTTPException:
        errstr += "HTTPException"
    except Exception, e:
        errstr += "Exception = " + str(traceback.format_exc()) + ", " + str(e.reason)
    else:
        fbase = filename.split(".")[0]
        try:
            f = file(homedir + fbase + ".upd", "wb")
        except Exception, e:
            errstr = "Problem during saving new version. File: " + homedir + fbase + ". Error: " + str(
                e) + " Traceback: " + str(traceback.format_exc())
        else:
            f.write(response)
            f.close()
            errstr = ""
    finally:
        if not errstr == "":
            logmsg.update(errstr)
            return False
        request.close()
    return True


def checkUpdate(filename):
    errstr = "Unable to get latest version info - "
    try:
        request = urllib2.urlopen(stp.github + "autoupdate.data")
        response = request.read().rstrip("\r\n")
    except urllib2.HTTPError, e:
        errstr += "HTTPError = " + str(e.reason)
    except urllib2.URLError, e:
        errstr += "URLError = " + str(e.reason)
    except httplib.HTTPException, e:
        errstr += "HTTPException"
    except Exception:
        errstr += "Exception = " + str(traceback.format_exc())
    else:
        errstr = ""
        t = response.split(":")

        new_hash = getHash(stp.homedir + str(t[1])).hexdigest()
        if new_hash == "":
            logmsg.update("Can't find file " + str(t[1]), 'E')
        else:
            try:
                tmp_ver = int(t[0])
            except Exception:
                tmp_ver = 0
            logmsg.update("Available file: " + str(t[1]) + ", V" + str(tmp_ver) + " with hash " + str(t[3]))
            logmsg.update("Actual version: " + str(stp.version) + ", hash: " + str(new_hash))
            if new_hash != t[3] and stp.version <= tmp_ver:
                var.logger.info("Downloading new version V" + str(tmp_ver))
                down_result = downloadFile(t[1])
                if down_result:
                    logmsg.update("V" + str(tmp_ver) + " downloaded. Hash is " + str(t[3]))
                    return 2
                else:
                    logmsg.update("Problem downloading new version. Result=" + str(down_result) + ", file=" + str(t[1]))
            else:
                return 1

    if not errstr == "":
        logmsg.update(errstr)
    return 0


def do_update(state, homedir):
    """
    Perform update
    :param state: boolean, is autoupdate enabled?
    :param homedir, string, home directory
    :return: boolean, True if something updated
    """
    updated = []
    upd_str = ""
    if state:
        for k in upd_files:
            chk = checkUpdate(k)
            if chk == 2:
                updated.append(k)
                upd_str += k + "<br/>"
                os.rename(homedir + k + ".upd", homedir + k + ".py")
        if len(updated) > 0:
            body = ("<h1>Device upgrade information.</h1>\n"
                    "   <p>Hello, I'm your thermostat and I have a news for you.<br/>\n"
                    "	Please take a note, that I found new version of app:<br/>\n" +
                    upd_str +
                    "   and I'll be upgraded in few seconds.</br>\n"
                    "	Resistance is futile :).<br/>")
            # sendWarning("upgrade", temp_key, body)
            return True
    else:
        logmsg.update("Auto update is disabled.")
    return False
