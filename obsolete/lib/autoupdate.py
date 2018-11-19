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


def download_file(get_file, put_file):
    err_str = ""
    try:
        request = urllib2.urlopen(get_file)
        response = request.read()
    except urllib2.HTTPError, e:
        err_str += "HTTPError = " + str(e.reason)
    except urllib2.URLError, e:
        err_str += "URLError = " + str(e.reason)
    except httplib.HTTPException:
        err_str += "HTTPException"
    except Exception, e:
        err_str += "Exception = " + str(traceback.format_exc()) + ". Error: " + str(e)
    else:
        tmp_dir = os.path.dirname(put_file)
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        try:
            f = file(put_file, "wb")
        except Exception, e:
            err_str = "Problem during saving new version. File: " + put_file + ". Error: " + str(
                e) + " Traceback: " + str(traceback.format_exc())
        else:
            f.write(response)
            f.close()
            err_str = ""
            request.close()
    finally:
        if not err_str == "":
            logmsg.update(err_str)
            return False
    return True


def check_update(version):
    github = "https://github.com/autopower/thermeq3/raw/master/install/current/"
    home_dir = "/root/thermeq3"
    err_str = "Unable to get latest version info - "

    try:
        request = urllib2.urlopen(github + "autoupdate.data")
        response = request.read().rstrip("\r\n")
    except urllib2.HTTPError, e:
        err_str += "HTTPError = " + str(e.reason)
    except urllib2.URLError, e:
        err_str += "URLError = " + str(e.reason)
    except httplib.HTTPException:
        err_str += "HTTPException"
    except Exception:
        err_str += "Exception = " + str(traceback.format_exc())
    else:
        err_str = ""
        t = response.split(":")

        new_hash = get_hash(home_dir + "-install/" + str(t[1])).hexdigest()
        if new_hash == "":
            logmsg.update("Can't find file " + str(t[1]), 'E')
        else:
            try:
                tmp_ver = int(t[0])
            except Exception:
                tmp_ver = 0
            logmsg.update("Available file: " + str(t[1]) + ", V" + str(tmp_ver) + " with hash " + str(t[3]), 'I')
            logmsg.update("Actual version: " + str(version) + ", hash: " + str(new_hash), 'I')
            if new_hash != t[3] and version < tmp_ver:
                logmsg.update("Downloading new version V" + str(tmp_ver))
                down_result = download_file(github + t[1], home_dir + "-install/" + t[1])
                if down_result:
                    logmsg.update("V" + str(tmp_ver) + " downloaded. Hash is " + str(t[3]))
                    return [2, t[1]]
                else:
                    logmsg.update("Problem downloading new version. Result=" + str(down_result) + ", file=" + str(t[1]))
            else:
                return [1, ""]

    if not err_str == "":
        logmsg.update(err_str)
    return [0, ""]


def do(version):
    """
    Perform update
    :param version: string
    :return: boolean, True if something updated
    """
    home_dir = "/root/thermeq3"
    chk, filename = check_update(version)
    result = False
    if chk == 2:
        # unzip files
        with zipfile.ZipFile(home_dir + "-install/" + filename, "r") as z:
            try:
                z.extractall(home_dir + "/")
            except Exception:
                logmsg.update("Error during archive extraction", 'E')
            else:
                logmsg.update("Archive successfully extracted.", 'I')
                result = True
    elif chk == 1:
        logmsg.update("Update is not necessary.")
    return result
