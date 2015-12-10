import urllib2
import traceback
import httplib
import logmsg
import os
import hashlib
import zipfile


def get_hash(filename):
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


def download_file(home_dir, filename):
    errstr = ""
    try:
        request = urllib2.urlopen(filename)
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
        try:
            f = file(home_dir + filename, "wb")
        except Exception, e:
            errstr = "Problem during saving new version. File: " + home_dir + filename + ". Error: " + str(
                e) + " Traceback: " + str(traceback.format_exc())
        else:
            f.write(response)
            f.close()
            errstr = ""
    finally:
        request.close()
        if not errstr == "":
            logmsg.update(errstr)
            return False
    return True


def checkUpdate(version, beta):
    if beta:
        github = "https://github.com/autopower/thermeq3/raw/master/install/beta/"
    else:
        github = "https://github.com/autopower/thermeq3/raw/master/install/"
    home_dir = "/root/thermeq3"
    errstr = "Unable to get latest version info - "
    try:
        request = urllib2.urlopen(github + "autoupdate.data")
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

        new_hash = get_hash(home_dir + "-install/" + str(t[1])).hexdigest()
        if new_hash == "":
            logmsg.update("Can't find file " + str(t[1]), 'E')
        else:
            try:
                tmp_ver = int(t[0])
            except Exception:
                tmp_ver = 0
            logmsg.update("Available file: " + str(t[1]) + ", V" + str(tmp_ver) + " with hash " + str(t[3]))
            if new_hash != t[3] and version <= tmp_ver:
                logmsg.update("Downloading new version V" + str(tmp_ver))
                down_result = download_file(home_dir, t[1])
                if down_result:
                    logmsg.update("V" + str(tmp_ver) + " downloaded. Hash is " + str(t[3]))
                    return [2, t[1]]
                else:
                    logmsg.update("Problem downloading new version. Result=" + str(down_result) + ", file=" + str(t[1]))
            else:
                return [1, ""]

    if not errstr == "":
        logmsg.update(errstr)
    return [0, ""]


def do(version, beta):
    """
    Perform update
    :param version: string
    :return: boolean, True if something updated
    """
    home_dir = "/root/thermeq3"
    chk, filename = checkUpdate(version, beta)
    if chk == 2:
        # unzip files
        with zipfile.ZipFile(home_dir + "-install/" + filename, "r") as z:
            z.extractall(home_dir + "/", "*.py")
        return True
    else:
        return False
