#!/usr/bin/env python
import platform
import subprocess
import os
import json
import urllib
import urllib2
import traceback

run_target = ""
cfg = {}


def check_for_locations(woeid, owm_api_key):
    """
    Returns weather from yahoo weather from given WOEID
    :param owm_api_key:
    :param woeid: integer, yahoo weather ID
    """
    city = "Error city"
    temp = None
    humidity = None

    if woeid is None:
        print("Wrong WOEID!")
    elif owm_api_key is None:
        print("OWM API key not set!")
    else:
        # please change u='c' to u='f' for fahrenheit below
        base_url = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
        yql_url = base_url + urllib.urlencode({'q': yql_query}) + "&format=json"

        try:
            result = urllib2.urlopen(yql_url).read()
            data = json.loads(result)
        except Exception, error:
            print("Yahoo communication error: " + str(error))
            print("Traceback: " + str(traceback.format_exc()))
        else:
            if data is not None:
                try:
                    city = data["query"]["results"]["channel"]["location"]["city"]
                    temp = int(data["query"]["results"]["channel"]["item"]["condition"]["temp"])
                    humidity = int(data["query"]["results"]["channel"]["atmosphere"]["humidity"])
                except Exception:
                    pass
                else:
                    # and check if yahoo is correct
                    url = "http://api.openweathermap.org/data/2.5/weather?q=" + str(city) + "&appid=" + owm_api_key + "&units=metric"
                    try:
                        result = json.load(urllib2.urlopen(url))
                    except Exception, error:
                        print("OWM communication error: " + str(error))
                        print("Traceback: " + str(traceback.format_exc()))
                        owm_id = -1
                    else:
                        if "main" in result and "id" in result:
                            owm_id = result["id"]
                            owm_temp = result["main"]["temp"]
                            yho_temp = temp
                            owm_humidity = result["main"]["humidity"]
                            if abs(yho_temp - owm_temp) > 1.5:
                                print("Difference between Yahoo and OWM temperatures. Yahoo=" + str(yho_temp) +
                                      " OWM=" + str(owm_temp))
                                # end check
                        else:
                            print("Error during parsing result.")
                        print("\tYahoo result: Current temperature in " + str(city) + " is " + str(temp) +
                              ", humidity " + str(humidity) + "%")
                        print("\tOWM result: Current temperature in " + str(city) + " is " + str(owm_temp) +
                              ", humidity " + str(owm_humidity) + "%")

    print("\tYahoo woeid: " + str(woeid))
    print("\tOWM city ID: " + str(owm_id))
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
    try:
        f = open(config_file, "w")
    except IOError:
        print("IOError during open file for writing!")
    json.dump(cfg, f)
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
            try:
                f = open(new_config_file, "w")
            except IOError:
                print("Error during writing new config file: " + new_config_file)
            else:
                json.dump(ncf, f)
                f.close()


def get_config(rew):
    global cfg

    input_string = [["max_ip", "IP address of Max! Cube"],
                    ["from_addr", "sender address [From]"],
                    ["to_addr", "recipient address [To]"],
                    ["mail_server", "mail server address"],
                    ["mail_port", "mail server port", 25],
                    ["from_pwd", "mail server password"],
                    ["device_name", "device name", "thermeq3"],
                    ["ext_port", "external port", 29080],
                    ["owm_api_key", "open weather API key"],
                    ["yahoo_location", "Yahoo location ID", 823123],
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
            if len(k) > 2 and rew is False:
                txt += k[1] + " (default: " + str(k[2]) + ")"
            elif k[0] in cfg:
                txt += k[1] + " (default: " + str(cfg[k[0]]) + ")"
            else:
                txt += k[1]
            value = raw_input("Please enter" + txt + ": ")
            if value == "" and len(k) > 2 or k[0] in cfg:
                if len(k) > 2:
                    value = k[2]
                elif k[0] in cfg:
                    value = cfg[k[0]]
                print("\tUsing defaults (" + str(value) + ").")
            if k[0] == "max_ip":
                if ping(str(value)) is False:
                    print("Cannot ping host " + str(value) + "!")
        config_str.update({k[0]: str(value)})

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
        ret_value = check_for_locations(cfg["yahoo_location"], cfg["owm_api_key"])
    else:
        ret_value = check_for_locations(cfg["location"], cfg["owm_api_key"])

    # and update owm location
    if "owm_location" in cfg:
        print("OWM location updated in config.")
    else:
        print("OWM location added to config.")
    cfg.update({"owm_location": ret_value})
    save(new)
    print("Config file saved into " + new)
