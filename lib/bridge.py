import sys
import os
import logmsg
import json


_result = False
if os.name == "posix":
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
            self.bridge_var = {}

        def get(self, key):
            if key in self.bridge_var:
                r = self.bridge_var[key]
            else:
                r = None
            return r

        def getall(self):
            return self.bridge_var

        def put(self, key, value):
            self.bridge_var.update({key: value})

bridge_client = BridgeClient()


# required values, if any error in bridge then defaults is used [1]
# format codeword: ["codeword in bridge", default value, literal processing, variable]
cw = {
    "mode": ["mode", "auto", True, "var.mode"],
    # valve position in % to start heating
    "valve": ["valve_pos", 35, True, "setup.valve_pos"],
    # start heating if single valve position in %, no matter how many valves are needed to start to heating
    "svpnmw": ["svpnmw", 75, True, "setup.svpnmw"],
    # how many valves must be in position stated above
    "valves": ["valves", 2, True, "setup.valves"],
    # if in total mode, sum of valves position to start heating
    "total": ["total_switch", 150, True, "setup.total_switch"],
    # preference, "per" = per valve, "total" to total mode
    "pref": ["preference", "per", True, "setup.preference"],
    # interval, seconds to read MAX!Cube
    "int": ["interval", 90, True, "setup.intervals['max'][0]"],
    #
    "ign_op": ["ignore_opened", 15, True, "eq3.ignore_time"],
    # use auto update function?
    "au": ["autoupdate", True, True, "setup.au"],
    # beta features on (yes) or off (no)
    "beta": ["beta", "no", True, "var.beta"],
    # profile type, time or temp, temp profile type means that external temperature (yahoo weather) is used
    "profile": ["profile", "time", False, ""],
    # list of ignored devices
    "ign": ["ignored", {}, True, "eq3.ignored_valves"],
    # no open window warning, if True then no window warning via email
    "no_oww": ["no_oww", 0, True, "setup.no_oww"],
    # heat time dictionary
    "ht": ["heattime", {}, True, "var.ht"],
    # communication errors, how many times failed communication between thermeq3 and MAX!Cube, 0 after sending status
    "errs": ["error", 0, False, ""],
    # same as above, but cumulative number
    "terrs": ["totalerrors", 0, False, ""],
    "cmd": ["command", "", False, ""],
    "msg": ["msg", "", False, ""],
    "uptime": ["uptime", "", False, ""],
    "appuptime": ["app_uptime", 0, False, ""],
    "status": ["status", "defaults", False, ""],
    "sys": ["system_status", {}, False, ""]
    }


def get_pcw():
    global cw
    lcw = {}
    for k, v in cw.iteritems():
        # key : [default, literal]
        lcw.update({v[0]: [v[1], v[2], v[3]]})
    return lcw

pcw = get_pcw()


def save(bridge_file):
    """
    Save bridge to bridge_file, if success return True, else False
    :param bridge_file: string
    :return: boolean
    """
    global bridge_client
    try:
        tmp = bridge_client.getall()
    except Exception:
        logmsg.update("Error reading bridge!", 'E')
    else:
        try:
            f = open(bridge_file, "w")
        except Exception:
            logmsg.update("Error writing to bridge file!", 'E')
        else:
            f.write(json.dumps(tmp, sort_keys=True))
            f.close()
            logmsg.update("Bridge file saved.", 'D')
            return True
    return False


def process_bridge_cw(codeword, def_value, set_value):
    global bridge_client
    # check if correct values are loaded
    if set_value == "" or set_value is None:
        result = def_value
    else:
        result = set_value
    # put bridge value
    bridge_client.put(codeword, result)


def load(bridge_file):
    """
    Load data from bridge_file and return dictionary or None
    :param bridge_file: string
    :return: dictionary
    """
    data = {}
    if os.path.exists(bridge_file):
        with open(bridge_file, "r") as f:
            try:
                data = json.load(f)
            except:
                pass
            finally:
                f.close()
        logmsg.update("Bridge file loaded.", 'D')
    else:
        logmsg.update("Error loading bridge file!", 'E')
        data = None
    return data


def get_cw(lcw):
    """
    Return codeword from dictionary
    :param lcw: key
    :return: string
    """
    global cw
    if lcw in cw:
        return str(cw[lcw][0])
    else:
        return "wrong_key " + str(lcw)


def get_cw_default(lcw):
    """
    Return codeword and default value from dictionary
    :param lcw: key
    :return: string
    """
    global cw
    if lcw in cw:
        return str(cw[lcw][0]), cw[lcw][1]
    else:
        return "wrong_key " + str(lcw), 0


def try_read(lcw, _save=True):
    """
    try read from bridge, if key not there, save default value
    :param lcw: string, local codeword
    :param _save: boolean, if not in bridge then save
    :return: various
    """
    global bridge_client, cw

    temp_cw, default = get_cw_default(lcw)
    tmp_str = bridge_client.get(temp_cw)

    if tmp_str == "None" or tmp_str == "" or tmp_str is None:
        tmp = default
        if _save:
            bridge_client.put(temp_cw, str(tmp))
    else:
        if type(default) is int:
            try:
                tmp = int(tmp_str)
            except Exception:
                tmp = default
        else:
            tmp = tmp_str
    return tmp


def put(key, value):
    """
    Put value to the key in bridge_client
    :param key: key
    :param value: string
    :return: nothing
    """
    global bridge_client
    bridge_client.put(get_cw(key), str(value))


def get(key):
    """
    Get from bridge_client by key, key is expanded through CW
    :param key: key
    :return:  string
    """
    global bridge_client
    return str(bridge_client.get(get_cw(key)))


def export():
    """
    Export bridge_client.json as JSON
    :return: JSON string
    """
    global bridge_client
    return json.dumps(bridge_client.getall())


def get_cmd():
    local_cmd = get("cmd")
    if local_cmd is None:
        return ""
    elif len(local_cmd) > 0:
        put("cmd", "")
    return local_cmd
