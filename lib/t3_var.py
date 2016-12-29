import time
import sys
import profiles
import traceback
import os
import errno
import bridge


class Thermeq3Status(object):
    def __init__(self):
        self.status_str = {
            "i": "idle",
            "h": "heating",
            "s": "starting",
            "d": "dead",
            "hv": "heating and ventilating",
            "iv": "idle and ventilating",
            "m": "manual"}
        self.actual = ''

    def update(self, status_key):
        """
        Update status string
        :param status_key: string, key in status_str
        :return: nothing
        """
        if status_key not in self.status_str:
            key_error_str = "Key error"
            bridge.put("status", key_error_str)
            self.actual = key_error_str
        else:
            bridge.put("status", self.status_str[status_key])
            bridge.put("status_key", status_key)
            self.actual = self.status_str[status_key]


class Thermeq3Setup(object):
    def __init__(self):
        # thermeq3 configuration variables, override in /root/config.py
        self.version = 231
        # please change to rpi for Raspberry Pi
        self.target = "yun"
        # window ignore time, in minutes
        self.window_ignore_time = 15
        # my IP address
        self.my_ip = "127.0.0.1"
        # sd card or usb key mount point, default is /mnt/sda1/
        self.place = ""
        # where is stderr log located, def setup.place+setup.devname+"_error.log"
        self.stderr_log = ""
        # difference from last known valve value, in %
        self.percentage = 3
        # github location for auto update
        self.github = "https://raw.github.com/autopower/thermeq3/master/"
        # home directory is /root
        self.homedir = "/root/"
        # abnormal count of warning is
        self.abnormalCount = 30
        # how many windows must be open to recognize that we are ventilating
        self.ventilate_num = 3
        self.timeout = 10
        self.ext_port = 80
        # which mode is selected: [TIME, TEMP, NORMAL]
        self.selected_mode = "TIME"
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

        # Required per-install variables, configured in /root/config.py
        # Reported name of this thermeq3 installation ie. "thermeq3"
        self.devname = None
        # MAX Cube
        # ie. "192.168.0.10"
        self.max_ip = None
        # e-mail
        # ie. "devices@foo.local"
        self.fromaddr = None
        # ie. "user@foo.local", or a list: ["user1@foo.local", user@bar.local]
        self.toaddr = None
        # SMTP host ie. "mail.foo.local"
        self.mailserver = None
        # SMTP port ie. 25
        self.mailport = None
        # SMTP authentication username, ie. "user@foo.local"
        self.mailuser = None
        # SMTP authentication password, ie. "password"
        self.mailpassword = None
        # Weather info
        # open weather map API key, ie "123456789"
        self.owm_api_key = None
        # geographic location, as per Yahoo WOEID. ie. "12345"
        self.location = None

        # import /root/config.py, overriding per-install variables above
        try:
            execfile("/root/config.py")
        except IOError:
            self.err_str = "Can't find config file or config file IO error!"
            sys.exit(self.err_str)
        except SyntaxError:
            self.err_str = "Syntax error in config file!"
            sys.exit(self.err_str)
        except NameError as err:
            detail = err.args[0]
            self.err_str = "Name error in config file!\n" + \
                           "Detail: " + str(detail) + "\n"
            sys.exit(self.err_str)
        except Exception as err:
            error_class = err.__class__.__name__
            detail = err.args[0]
            cl, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]
            self.err_str = "Can't find config file or config file error!\n" + \
                           "Detail: " + str(error_class) + "\n" + str(detail) + "\n" + \
                           str(cl) + "\n" + str(exc) + "\n" + str(tb) + "\n" + \
                           str(line_number) + "\n"
            sys.exit(self.err_str)

        if not self.init_paths():
            self.err_str = "Error: can't find mounted storage device!\n" + \
                           "Please mount SD card or USB key and run program again."

        try:
            os.makedirs(self.place + "www")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def init_paths(self):
        if os.name == "nt":
            if os.path.exists("t:/mnt/sda1"):
                self.place = "t:/mnt/sda1/"
            elif os.path.exists("t:/mnt/sdb1"):
                self.place = "t:/mnt/sdb1/"
            else:
                return False
            # init path variables
            self.log_filename = self.place + self.devname + ".log"
            self.csv_log = self.place + "csv/" + self.devname + ".csv"
            self.bridge_file = self.place + self.devname + ".bridge"
            self.stderr_log = self.place + self.devname + "_error.log"
            return True
        else:
            if self.target == "yun":
                if os.path.exists("/mnt/sda1"):
                    self.place = "/mnt/sda1/"
                elif os.path.exists("/mnt/sdb1"):
                    self.place = "/mnt/sdb1/"
                else:
                    return False
                # init path variables
                self.log_filename = self.place + self.devname + ".log"
                self.csv_log = self.place + "csv/" + self.devname + ".csv"
                self.bridge_file = self.place + self.devname + ".bridge"
                self.stderr_log = self.place + self.devname + "_error.log"
                return True
            elif self.target == "rpi":
                # TBI RPI
                # please update path according to RPi environment
                if os.path.exists("/mnt/sda1"):
                    self.place = "/mnt/sda1/"
                elif os.path.exists("/mnt/sdb1"):
                    self.place = "/mnt/sdb1/"
                else:
                    return False
                # init path variables
                self.log_filename = self.place + self.devname + ".log"
                self.csv_log = self.place + "csv/" + self.devname + ".csv"
                self.bridge_file = self.place + self.devname + ".bridge"
                self.stderr_log = self.place + self.devname + "_error.log"
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
        # heat times; total: [totalheattime, time.time()]
        self.ht = {}
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
