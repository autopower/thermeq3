#!/usr/bin/env python
import platform
import subprocess
import os
import json
import urllib
import urllib2
import traceback
import uuid
import hmac
import hashlib
import time
from base64 import b64encode


run_target = ""
cfg = {}


# noinspection PyBroadException
def get_yahoo_data(woe_id, yahoo_data):
    city = "Error"
    if woe_id is None:
        city = "WOEID None"
    else:
        # basic info
        url = 'https://weather-ydn-yql.media.yahoo.com/forecastrss'
        method = 'GET'
        try:
            data = json.loads(yahoo_data)
        except Exception:
            pass
        else:
            app_id = str(data["app_id"])
            consumer_key = str(data["consumer_key"])
            consumer_secret = str(data["consumer_secret"])
            concat = '&'
            query = {'woeid': str(woe_id), 'format': 'json', 'u': 'c'}
            oauth = {
                'oauth_consumer_key': consumer_key,
                'oauth_nonce': uuid.uuid4().hex,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_version': '1.0'
            }

            # Prepare signature string (merge all params and SORT them)
            merged_params = query.copy()
            merged_params.update(oauth)
            sorted_params = [k + '=' + urllib.quote(merged_params[k], safe='') for k in sorted(merged_params.keys())]
            signature_base_str = method + concat + urllib.quote(url, safe='') + concat + urllib.quote(
                concat.join(sorted_params), safe='')

            # Generate signature
            composite_key = urllib.quote(consumer_secret, safe='') + concat
            oauth_signature = b64encode(hmac.new(composite_key, signature_base_str, hashlib.sha1).digest())

            # Prepare Authorization header
            oauth['oauth_signature'] = oauth_signature
            auth_header = 'OAuth ' + ', '.join(['{}="{}"'.format(k, v) for k, v in oauth.iteritems()])

            # Send request
            url = url + '?' + urllib.urlencode(query)
            request = urllib2.Request(url)
            request.add_header('Authorization', auth_header)
            request.add_header('Yahoo-App-Id', app_id)
            try:
                data = urllib2.urlopen(request).read()
            except Exception, error:
                pass
            else:
                if data is not None:
                    data = json.loads(data)
                    try:
                        city = data["location"]["city"]
                    except Exception:
                        pass

    return city


def get_owm_data(city, owm_api_key):
    owm_id = None

    if owm_api_key is None:
        print("OWM API key not set!")
    else:
        # and check if yahoo is correct
        url = "http://api.openweathermap.org/data/2.5/weather?q=" + str(city) + "&appid=" + owm_api_key + \
              "&units=metric"
        try:
            result = json.load(urllib2.urlopen(url))
        except Exception, error:
            print("OWM communication error: " + str(error))
            print("Traceback: " + str(traceback.format_exc()))
            owm_id = -1
        else:
            if "main" in result and "id" in result:
                owm_id = result["id"]
            else:
                print("Error during parsing result.")

    return str(owm_id)


def guess_platform():
    """
    Returns platform in global variable
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


def ping(host):
    """
    Returns True if host responds to a ping request
    """
    # Ping parameters as function of OS
    ping_str = "-n 1" if platform.system().lower() == "windows" else "-c 1"
    args = "ping " + " " + ping_str + " " + host
    need_sh = False if platform.system().lower() == "windows" else True
    # Ping
    return subprocess.call(args, shell=need_sh) == 0


def load(config_file):
    f = None
    result = {}
    try:
        f = open(config_file, "r")
    except IOError:
        pass
    else:
        if f is not None:
            result = json.load(f)
    finally:
        if f is not None:
            f.close()
    return result


def save(config_file):
    global cfg

    write_to_file(config_file, cfg)


def load_yahoo():
    global cfg
    if "yahoo" in cfg:
        tmp = json.loads(cfg["yahoo"])
        cfg.update({"app_id": tmp["app_id"]})
        cfg.update({"consumer_key": tmp["consumer_key"]})
        cfg.update({"consumer_secret": tmp["consumer_secret"]})


def write_to_file(file_name, file_payload):
    try:
        f = open(file_name, "w")
    except IOError:
        print("Error during writing file: " + file_name)
    else:
        json.dump(file_payload, f)
        f.close()


def load_old(old_config_file, new_config_file):
    cf_1 = ["self.devname", "self.max_ip", "self.fromaddr", "self.toaddr", "self.mailserver", "self.mailport",
            "self.frompwd", "self.owm_api_key", "self.location", "self.extport"]
    cf_2 = ["self.device_name", "self.max_ip", "self.from_addr", "self.to_addr", "self.mail_server", "self.mail_port",
            "self.from_pwd", "self.owm_api_key", "self.yahoo_location", "self.ext_port"]
    ncf = {}
    if os.path.exists(old_config_file):
        try:
            f = open(old_config_file, "r")
        except IOError:
            print("IOError during opening olf config file: " + old_config_file)
        else:
            num = 0
            for line in f:
                is_comment = line.find('#')
                if is_comment == 0:
                    pass
                else:
                    if is_comment > 0:
                        line = line[:-is_comment]
                    w = line.split("=")
                    wr = w[0].rstrip()
                    if not w[0] == "\n":
                        if "toaddr" in wr:
                            wv = w[1].lstrip().rstrip()
                        else:
                            wv = w[1].lstrip().rstrip().replace('"', '')
                        if wr in cf_1:
                            num += 1
                            idx = cf_1.index(wr)
                            ncf.update({cf_2[idx].replace("self.", ""): str(wv)})
            if num < len(cf_1):
                # some commands are missing
                print("Old config file is incomplete, some command missing!")
            else:
                # everything is ok
                print("New config file created, now saving...")
            f.close()
            write_to_file(new_config_file, ncf)


def get_config(rew):
    global cfg

    input_string = [["max_ip", "IP address of Max! Cube"],
                    ["from_addr", "sender address [From]"],
                    ["to_addr", "recipient address [To]"],
                    ["mail_server", "mail server address"],
                    ["mail_port", "mail server port", 25],
                    ["from_user", "mail server user"],
                    ["from_pwd", "mail server password"],
                    ["device_name", "device name", "thermeq3"],
                    ["ext_port", "external port", 29080],
                    ["owm_api_key", "open weather API key"],
                    ["yahoo_location", "Yahoo location ID", 823123],
                    ["app_id", "Yahoo AppID"],
                    ["consumer_key", "Yahoo consumer key"],
                    ["consumer_secret", "Yahoo consumer secret"],
                    ["csv_values", ":\n1 if only set temp\n2 if only actual temp\n3 both temp\nis written into csv", 1],
                    ["hard_ignored", "valve ID to ignore forever (q to quit)"]]

    config_str = {}
    ignored = {}
    for k in input_string:
        if k[0] == "hard_ignored":
            value = ""
            while not value == "q":
                value = raw_input("Please enter " + k[1] + ": ")
                if value == "q":
                    pass
                else:
                    ignored.update({str(value): 1924991999})
            value = json.dumps(ignored)
        else:
            txt = " "
            if len(k) > 2 and rew is True:
                txt += k[1] + " (default: " + str(k[2]) + ")"
            elif k[0] in cfg:
                txt += k[1] + " (default: " + str(cfg[k[0]]) + ")"
            else:
                txt += k[1]
            value = raw_input("Please enter" + txt + ": ")
            if value == "" and (len(k) > 2 or k[0] in cfg):
                if len(k) > 2 and rew is True:
                    value = k[2]
                elif k[0] in cfg:
                    value = cfg[k[0]]
                print("\tUsing defaults (" + str(value) + ").")
            if k[0] == "max_ip":
                if ping(str(value)) is False:
                    print("Cannot ping host " + str(value) + "!")
        config_str.update({k[0]: str(value)})

    tmp_yahoo = {"app_id": cfg["app_id"],
                 "consumer_key": cfg["consumer_key"],
                 "consumer_secret": cfg["consumer_secret"]}
    config_str.update({"yahoo": json.dumps(tmp_yahoo)})
    del config_str["app_id"]
    del config_str["consumer_key"]
    del config_str["consumer_secret"]

    print("Final config string:\n" + json.dumps(config_str))
    cfg = config_str


def do_config(file_name, rewrite):
    get_config(rewrite)
    save(file_name)
    print("Config file saved into " + file_name)


if __name__ == '__main__':
    print("thermeq3 interactive config\n")
    guess_platform()
    print("Platform is " + str(run_target))
    if run_target == "win":
        old = "t:/root/config.py"
        new = "t:/root/thermeq3.json"
    else:
        old = "/root/config.py"
        new = "/root/thermeq3.json"
    # just for testing
    print("Using " + old + " as old and " + new + " as new config file")
    if os.path.exists(new) and "test" in new:
        print("It looks like you testing config. Deleting file " + new)
        os.remove(new)
    # testing end

    if os.path.exists(old):
        print("Old config file found.")
        load_old(old, new)
        if run_target == "win":
            cmd = "ren " + old + " config.old"
            os.system(cmd.replace("/", "\\"))
        else:
            os.system("mv " + old + " /root/config.old")
    elif os.path.exists(new) is False:
        # if nothing exist in old config file and there is no new config file, get config
        print("There is no new config file!")
        do_config(new, True)
        save(new)
    else:
        print("New config file " + new + " found.")
        ret_value = raw_input("Replace config file [N/y]:").upper()
        if ret_value == "" or ret_value == "N":
            print("You choose keep current config file.")
        elif ret_value == "Y":
            cfg = load(new)
            load_yahoo()
            print("Backuping old config file...")
            if run_target == "win":
                cmd = "ren " + new + " thermeq3.bak"
                os.system(cmd.replace("/", "\\"))
            else:
                os.system("mv " + new + " /root/thermeq3.jsonbackup")
            do_config(new, False)
            save(new)

    # check weather location
    print("Loading config file to check weather:")
    cfg = load(new)
    if "yahoo_location" in cfg:
        # ret_value = check_for_locations(cfg["yahoo_location"], cfg["owm_api_key"])
        ret_value = get_yahoo_data(cfg["yahoo_location"], cfg["yahoo"])
        ret_value = get_owm_data(ret_value, cfg["owm_api_key"])
        if ret_value is not None:
            # and update owm location
            if "owm_location" in cfg:
                print("OWM location updated in config.")
            else:
                print("OWM location added to config.")
            cfg.update({"owm_location": ret_value})
            save(new)
    print("Config file saved into " + new)

    # prepare location.json file
    tmp_location = {"yahoo_location": cfg["yahoo_location"], "yahoo": cfg["yahoo"]}
    tmp_path = os.path.dirname(new) + "/location.json"
    write_to_file(tmp_path, tmp_location)
