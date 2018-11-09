import time
import sys
import profiles
import os
import errno
import bridge
import support
import config


class Thermeq3Status(object):
    def __init__(self):
        self.status_str = {
            "i": "idle",
            "h": "heating",
            "s": "starting",
            "d": "dead",
            "hv": "heating and ventilating",
            "iv": "idle and ventilating",
            "m": "manual",
            "e": "Error: ["}
        self.actual = ''

    def update(self, status_key, add_error=""):
        """
        Update status string
        :param status_key: string, key in status_str
        :param add_error: string, additional error info
        :return: nothing
        """
        if status_key not in self.status_str:
            _tmp_str = "Key error"
        else:
            _tmp_str = self.status_str[status_key]
            if status_key == "e":
                _tmp_str += add_error + "]"
        bridge.put("status", _tmp_str)
        bridge.put("status_key", status_key)
        self.actual = _tmp_str


class Thermeq3Setup(object):
    def __init__(self):
        # thermeq3 configuration variables, theres no override in /root/config.py
        self.version = 279
        # window ignore time, in minutes
        self.window_ignore_time = 15
        # my IP address
        self.my_ip = "127.0.0.1"
        # sd card or usb key mount point, default is /mnt/sda1/
        self.place = ""
        # where is stderr log located, default setup.place + setup.device_name + "_error.log"
        self.stderr_log = ""
        # difference from last known valve value, in %
        self.percentage = 3
        # abnormal count of warning is
        self.abnormalCount = 30
        # how many windows must be open to recognize that we are ventilating
        self.ventilate_num = 3
        self.timeout = 10
        self.ext_port = 80
        # which mode is selected: [TIME, TEMP, NORMAL]
        self.selected_mode = "init"
        # control values
        self.preference = "per"
        self.valve_switch = 35
        # single valve position, no matter what
        self.svpnmw = 80
        self.total_switch = 150
        self.valve_num = 2
        self.au = True
        self.ignore_time = 30
        self.no_oww = False
        self.log_filename = ""
        self.csv_log = ""
        self.bridge_file = ""
        self.intervals = {}
        self.temp = []
        self.day = []
        # hard coded ignored valves
        self.hard_ignored = {}
        # which values will be written into csv file (1 = actual temp, 2 = set temp, 3 = both)
        self.csv_values = 1

        # Required per-install variables, configured in /root/config.py
        # Reported name of this thermeq3 installation ie. "thermeq3"
        self.device_name = "thermeq3"
        # MAX Cube
        # ie. "192.168.0.10"
        self.max_ip = None
        # e-mail
        # ie. "devices@foo.local"
        self.from_addr = None
        # ie. "user@foo.local", or a list: ["user1@foo.local", user@bar.local]
        self.to_addr = None
        # SMTP host ie. "mail.foo.local"
        self.mail_server = None
        # SMTP port ie. 25
        self.mail_port = None
        # SMTP authentication user, ie. "password"
        self.from_user = None
        # SMTP authentication password, ie. "password"
        self.from_pwd = None
        # Weather info
        # open weather map API key, ie "123456789"
        self.owm_api_key = None
        # geographic location, as per Yahoo WOEID. ie. "12345"
        self.yahoo_location = None
        self.owm_location = None
        # which weather value will be used as reference
        self.weather_reference = "yahoo"

        self.err_str = ""

        support.guess_platform()
        # import /root/config.py, overriding per-install variables above
        if support.is_win():
            # execfile("t:/root/config.py")
            old = "t:/root/config.py"
            new = "t:/root/thermeq3.json"
        else:
            # execfile("/root/config.py")
            old = "/root/config.py"
            new = "/root/thermeq3.json"

        result = config.load_old(old, new)
        if result == 1:
            self.err_str = "Info: can't find old config file.\n"
        elif result == 2:
            self.err_str = "Info: error processing old config file.\n"
        elif result == 3:
            self.err_str = "Info: you can't see something like this.\n"
        elif result == 4:
            self.err_str = "Info: error processing new config file.\n"
        elif result == 0:
            if support.is_win():
                cmd = "ren " + old + " config.old"
                os.system(cmd.replace("/", "\\"))
            else:
                os.system("mv " + old + " /root/config.old")

        #
        # seems everything is OK, so load config
        #
        result = config.load(new)
        if result == {}:
            self.err_str += "Error: can't find or load config file!\nPlease run config_me.py"
            sys.exit(self.err_str)
        else:
            try:
                obj = eval("self")
            except SyntaxError:
                self.err_str += "Error while evaluating object!"
                sys.exit(self.err_str)
            else:
                for k, v in result.iteritems():
                    try:
                        if str(v).isdigit():
                            vs = int(v)
                        else:
                            vs = str(v)
                        setattr(obj, str(k), vs)
                    except NameError:
                        pass
        # check from_user and from_addr combinations
        if self.from_user is None or self.from_user == "":
            self.from_user = self.from_addr
            pass
        if self.from_addr is None or self.from_addr == "":
            self.from_addr = self.from_user + "@thermeq3.world"

        # check if SD or USB is mounted, if not raise error
        if not self.init_paths():
            self.err_str = "Error: can't find mounted storage device!\n" + \
                           "Please mount SD card or USB key and run program again.\n"

        # create www directory, if now www directory exist raise error
        try:
            os.makedirs(self.place + "www")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                self.err_str = "Error: can't create www directory!\nPlease check mounted storage device."
                raise

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def init_paths(self):
        # for new platform uncomment these lines below
        # print support.is_win(), support.is_yun(), support.is_rpi()
        # print os.path.ismount("/mnt/sda1"), os.path.ismount("/mnt/sdb1")
        if support.is_win():
            if os.path.exists("t:/mnt/sda1"):
                self.place = "t:/mnt/sda1/"
            elif os.path.exists("t:/mnt/sdb1"):
                self.place = "t:/mnt/sdb1/"
            else:
                return False
            # init path variables
            self.log_filename = self.place + self.device_name + ".log"
            self.csv_log = self.place + "csv/" + self.device_name + ".csv"
            self.bridge_file = self.place + self.device_name + ".bridge"
            self.stderr_log = self.place + self.device_name + "_error.log"
            return True
        elif support.is_yun():
            if os.path.ismount("/mnt/sda1") or os.path.isdir("/mnt/sda1"):
                self.place = "/mnt/sda1/"
            elif os.path.ismount("/mnt/sdb1") or os.path.isdir("/mnt/sdb1"):
                self.place = "/mnt/sdb1/"
            else:
                return False
            # init path variables
            self.log_filename = self.place + self.device_name + ".log"
            self.csv_log = self.place + "csv/" + self.device_name + ".csv"
            self.bridge_file = self.place + self.device_name + ".bridge"
            self.stderr_log = self.place + self.device_name + "_error.log"
            return True
        elif support.is_rpi():
            # TBI RPI
            # please update path according to RPi environment
            if os.path.ismount("/mnt/sda1") or os.path.isdir("/mnt/sda1"):
                self.place = "/mnt/sda1/"
            elif os.path.ismount("/mnt/sdb1") or os.path.isdir("/mnt/sdb1"):
                self.place = "/mnt/sdb1/"
            else:
                return False
            # init path variables
            self.log_filename = self.place + self.device_name + ".log"
            self.csv_log = self.place + "csv/" + self.device_name + ".csv"
            self.bridge_file = self.place + self.device_name + ".bridge"
            self.stderr_log = self.place + self.device_name + "_error.log"
            return True

    def init_intervals(self):
        # threshold in seconds, so 10 minutes are 10*60 seconds
        # interval as "name": [interval=how often check, mute int, next_time]
        tm = time.time()
        self.intervals = {
            "max": [120, 0, tm],
            "upg": [4 * 60 * 60, 0, tm],
            "var": [10 * 60, 0, tm],
            # threshold, send every X, muted for X
            "oww": [10 * 60, 30 * 60, 60 * 60],
            # threshold, muted for X, time.time()
            "wrn": [6 * 60 * 60, 24 * 60 * 60, tm],
            "err": [0, 0, 0.0],
            # sleep value
            "slp": [30, 3, tm]}
        # day windows/intervals
        # day = [0/from_str, 1/to_str, 2/total or per, 3/mode ("total"/"per"), 4/check interval, 5/valves]
        self.day = [
            ["00:00", "06:00", 34, "per", 180, 2],
            ["06:00", "10:00", 36, "per", 90, 2],
            ["10:00", "16:00", 38, "per", 120, 2],
            ["16:00", "22:00", 36, "per", 90, 2],
            ["22:00", "23:59", 34, "per", 120, 2]]
        # temperature table
        self.temp = [
            [-30, -20, 20, "per", 90, 2],
            [-20, -10, 25, "per", 120, 2],
            [-10, 0, 28, "per", 120, 2],
            [0, 10, 30, "per", 180, 2],
            [10, 20, 40, "per", 240, 2],
        ]
        profiles.init(self.day, self.temp)


class Thermeq3Variables(object):
    def __init__(self):
        self.appStartTime = time.time()
        # heat time for current day as list [date, time.time()]
        self.ht = {}
        # total: time.time()
        self.tht = float(0)
        # device log, used to count if valve position didn't change
        self.dev_log = {}
        # message queue
        self.msgQ = []
        # index in mode table
        self.act_mode_idx = -1
        # variable for weather situation
        self.situation = {}
        # CSV file
        self.csv = None
        # number of readings when we heating
        self.heat_readings = 0
        # heating is off
        self.heating = False
        # and we are not ventilating
        self.ventilating = False

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
