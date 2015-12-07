import sys
import time
import datetime
import os
import logmsg
import json


_result = False
if os.name != "nt":
    try:
        sys.path.insert(0, "/usr/lib/python2.7/bridge/")
        from bridgeclient import BridgeClient
        _result = True
    except:
        _result = False

if not _result:
    # if exception, it means no yun, abstraction to bridge, simplyfied code of arduino yun
    class BridgeClient:
        def __init__(self):
            self.json = {}

        def get(self, key):
            if key in self.json:
                r = self.json[key]
            else:
                r = None
            return r

        def put(self, key, value):
            self.json.update({key: value})

bridgeclient = BridgeClient()

cw = {
    """ required values, if any error in bridge then defaults is used [1]
    format codeword: ["codeword in bridge", default value, literal processing] """
    # thermeq3 mode, auto or manual
    "mode": ["mode", "auto", False],
    # valve position in % to start heating
    "valve": ["valve_pos", 35, False],
    # start heating if single valve position in %, no matter how many valves are needed to start to heating
    "svpnmw": ["svpnmw", 75, False],
    # how many valves must be in position stated above
    "valves": ["valves", 2, False],
    # if in total mode, sum of valves position to start heating
    "total": ["total_switch", 150, False],
    # preference, "per" = per valve, "total" to total mode
    "pref": ["preference", "per", False],
    # interval, seconds to read MAX!Cube
    "int": ["interval", 90, False],
    #
    "ign_op": ["ignore_opened", 15, False],
    # use autoupdate function?
    "au": ["autoupdate", True, False],
    # beta features on (yes) or off (no)
    "beta": ["beta", "no", False],
    # profile type, time or temp, temp profile type means that external temperature (yahoo weather) is used
    "profile": ["profile", "time", False],
    "no_oww": ["no_oww", 0, False],
    #
    # optional values
    #
    "ht": ["heattime",
           {"total": [0, 0.0], datetime.datetime.date(datetime.datetime.now()).strftime("%d-%m-%Y"): [0, time.time()]},
           True],
    # communication errors, how many times failed communication between thermeq3 and MAX!Cube, 0 after sending status
    "errs": ["error", 0, False],
    # same as above, but cumulative number
    "terrs": ["totalerrors", 0, False],
    "cmd": ["command", "", False],
    "msg": ["msg", "", False],
    "uptime": ["uptime", "", False],
    "appuptime": ["app_uptime", 0, False],
    "htstr": ["heattime_string", str(datetime.timedelta(seconds=0)), False],
    "daily": ["daily", "", False],
    "status": ["status", "defaults", False],
    "cur": ["current_status", "{}", False],
    # list of ignored devices
    "ign": ["ignored", "{}", True]}


def save(bridgefile):
    global bridgeclient, cw
    try:
        f = open(bridgefile, "w")
    except Exception:
        logmsg.update("Error writing to bridgefile!", 'E')
    else:
        for k, v in cw.iteritems():
            try:
                tmp = bridgeclient.get(v[0])
            except Exception:
                tmp = ""
            if tmp == "None" or tmp is None:
                tmp = str(v[1])
            f.write(v[0] + "=" + str(tmp) + "\r\n")
        f.close()
        return True


def process_bridge_cw(codeword, def_value, set_value):
    global bridgeclient
    result = ""
    # check if correct values are loaded
    if set_value == "" or set_value is None:
        result = def_value
    else:
        result = set_value
    # put bridge value
    bridgeclient.put(codeword, result)


def load(bridgefile):
    global bridgeclient, cw
    # prepare dictionary
    lcw = {}
    for k in cw.iteritems():
        # key : [default, literal]
        lcw.update({k[1][0]: [k[1][1], k[1][2]]})

    if os.path.exists(bridgefile):
        with open(bridgefile, "r") as f:
            for line in f:
                t = (line.rstrip("\r\n")).split('=')
                localcw = t[0]
                setvalue = t[1]
                if localcw in lcw:
                    process_bridge_cw(localcw, lcw[localcw][0], setvalue)
            f.close()
        logmsg.update("Bridge file loaded.", 'D')
    # >>>>>>> updateAllTimes()
    else:
        for k, v in lcw.iteritems():
            process_bridge_cw(k, v[0], v[0])
        logmsg.update("Error loading bridge file, using defaults!", 'E')


def rcw(lcw):
    """
    Return codeword from dictionary
    :param lcw: key
    :return:
    """
    """ returns command word, always string """
    global cw
    if lcw in cw:
        return str(cw[lcw][0])
    else:
        return "wrong_key"


def try_read(lcw, default, _save):
    """
    try read from bridge, if not there, save default value
    :param lcw: string, local codeword
    :param default: default value, various
    :param _save: boolean, if not in bridge save
    :return: various
    """
    global bridgeclient, cw
    if type(default) is str:
        isnum = False
    else:
        isnum = True
    temp_cw = rCW(lcw)

    tmp_str = bridgeclient.get(temp_cw)

    if tmp_str == "None" or tmp_str == "" or tmp_str is None:
        tmp = default
        if _save:
            bridgeclient.put(temp_cw, str(tmp))
    else:
        if isnum:
            try:
                tmp = int(tmp_str)
            except Exception:
                tmp = default
        else:
            tmp = tmp_str
    return tmp


def put(key, value):
    """
    Put value to the key in bridgeclient
    :param key: key
    :param value: string
    :return: nothing
    """
    global bridgeclient
    bridgeclient.put(rcw(key), str(value))


def get(key):
    """
    Get from bridgeclient by key, key is expanded through CW
    :param key: key
    :return:  string
    """
    global bridgeclient
    return str(bridgeclient.get(rcw(key)))


def export():
    """
    Export bridgeclient.json as JSON
    :return: JSON string
    """
    global bridgeclient
    return json.dumps(bridgeclient.json)


def import_(config_str):
    """
    Import config_str into bridgeclient.json dictionary
    :param config_str: string/json
    :return: boolean
    """
    global bridgeclient
    result = False
    try:
        tmp = json.loads(config_str)
    except ValueError:
        logmsg.update("Error during importing JSON.", 'E')
    else:
        result = True
        bridgeclient.json.update(tmp)

    return result
