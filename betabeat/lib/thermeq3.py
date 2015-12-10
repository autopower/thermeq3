import maxeq3
import time
import os
import datetime
import bridge
import logmsg
import weather
import public_ip
import errno
import mailer
from ast import literal_eval
import profiles
import autoupdate
# import action

err_str = ""


class thermeq3_status(object):
    def __init__(self):
        self.statusMsg = {
            "i": "idle",
            "h": "heating",
            "s": "starting",
            "d": "dead",
            "hv": "heating and ventilating",
            "iv": "idle and ventilating",
            "m": "manual"}
        self.actual = ''

    def update(self, statmsg):
        bridge.put("status", self.statusMsg[statmsg])
        self.actual = self.statusMsg[statmsg]


class thermeq3_setup(object):
    def __init__(self):
        self.version = 200
        self.target = "yun"
        # window ignore time, in minutes
        self.window_ignore_time = 15
        # my IP address
        self.myip = "127.0.0.1"
        # sd card or usb key mount point, default is /mnt/sda1/
        self.place = ""
        # where is stderr log located, def stp.place+stp.devname+"_error.log"
        self.stderr_log = ""
        # update this to your location, yahoo WOEID
        self.location = 818717
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
        """ this is in config.py file, here just for set type """
        self.max_ip = ""
        self.fromaddr = ""
        self.toaddr = ""
        self.mailserver = ""
        self.mailport = 25
        self.frompwd = ""
        self.devname = ""
        self.timeout = 10
        self.extport = 80
        # which mode is selected
        self.selectedMode = "TIME"
        # control values
        self.preference = "per"
        self.valve_switch = 35
        self.svpnmw = 80
        self.total_switch = 150
        self.valve_num = 2
        self.au = True
        self.ignore_time = 30
        self.no_oww = False
        self.log_filename = ""
        self.csv_log = ""
        self.bridgefile = ""
        self.secweb = {}
        self.intervals = {}
        self.temp = []
        self.day = []

    def init_paths(self):
        if os.name == "nt":
            if os.path.exists("d:/mnt/sda1"):
                self.place = "d:/mnt/sda1/"
            elif os.path.exists("d:/mnt/sdb1"):
                self.place = "d:/mnt/sdb1/"
            else:
                return False
            # init path variables
            self.log_filename = self.place + self.devname + ".log"
            self.csv_log = self.place + self.devname + ".csv"
            self.bridgefile = "d:/root/" + self.devname + ".bridge"
            self.stderr_log = self.place + self.devname + "_error.log"
            self.secweb = {
                "status": str(self.place + "www/status.xml"),
                "owl": str(self.place + "www/owl.xml"),
                "nice": str(self.place + "www/nice.html")}
            return True
        else:
            if self.target == "yun":
                if os.path.ismount("/mnt/sda1"):
                    self.place = "/mnt/sda1/"
                elif os.path.ismount("/mnt/sdb1"):
                    self.place = "/mnt/sdb1/"
                else:
                    return False
                # init path variables
                self.log_filename = self.place + self.devname + ".log"
                self.csv_log = self.place + self.devname + ".csv"
                self.bridgefile = "/root/" + self.devname + ".bridge"
                self.secweb = {
                    "status": str(self.place + "www/status.xml"),
                    "owl": str(self.place + "www/owl.xml"),
                    "nice": str(self.place + "www/nice.html")}
                return True
            elif self.target == "rpi":
                pass

    def init_intervals(self):
        # threshold in seconds, so 10 minutes are 10*60 seconds
        # interval as "name": [interval=how often check, mute int, next_time]
        tm = time.time()
        self.intervals = {
            "max": [120, 0, tm],
            "upg": [4 * 60 * 60, 0, tm],
            "var": [10 * 60, 0, tm],
            # threshold, send every X, muted for X
            "oww": [15 * 60, 45 * 60, 45 * 60],
            # threshold, muted for X, time.time()
            "wrn": [6 * 60 * 60, 24 * 60 * 60, tm],
            "err": [0, 0, 0.0],
            # just sleep value, always calculated as max[0] / slp[1]
            "slp": [40, 3, 0]}
        # day windows/intervals
        # day = [0-from_str, 1-to_str, 2-total or per, 3-mode ("total"/"per"), 4-check interval, 5-valves]
        self.day = [
            ["00:00", "06:00", 35, "per", 240, 1],
            ["06:00", "10:00", 36, "per", 120, 1],
            ["10:00", "14:00", 30, "per", 120, 2],
            ["14:00", "22:00", 36, "per", 120, 1],
            ["22:00", "23:59", 35, "per", 120, 1]]
        # temperature table
        self.temp = [
            [-30, -20, 20, "per", 90, 2],
            [-20, -10, 25, "per", 120, 2],
            [-10, 0, 28, "per", 120, 2],
            [0, 10, 30, "per", 180, 2],
            [10, 20, 40, "per", 240, 2],
        ]
        profiles.init(self.day, self.temp)

    def get_mail_data(self):
        return {"f": self.fromaddr, "t": self.toaddr, "sr": self.mailserver, "p": self.mailport, "pw": self.frompwd,
                "d": self.devname}


class thermeq3_variables(object):
    def __init__(self):
        self.appStartTime = time.time()
        # heat times; total: [totalheattime, time.time()]
        self.ht = {"total": [0, 0.0]}
        # device log, used to count if valve position didn't change
        self.dev_log = {}
        # message queue
        self.msgQ = []
        # index in mode table
        self.actModeIndex = -1
        # variable for weather situation
        self.situation = {}
        # CSV file
        self.csv = None
        # number of readings when we heating
        self.heatReadings = 0
        # heating is off
        self.heating = False
        # and we are not ventilating
        self.ventilating = False
        # clear errors
        self.err2Clear = False
        self.err2LastStatus = False
        self.error = False


class thermeq3_object(object):

    def __init__(self):
        global err_str
        self.eq3 = None
        self.setup = thermeq3_setup()
        self.var = thermeq3_variables()
        self.status = thermeq3_status()

        # import configuration
        try:
            execfile("/root/config.py")
        except:
            err_str = "Can't find config file!"
            print err_str
            exit()

        if not self.setup.init_paths():
            err_str = "Error: can't find mounted storage device! Please mount SD card or USB key and run program again."

        try:
            os.makedirs(self.setup.place + "www")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def prepare(self):
        self.setup.init_intervals()
        logmsg.start(self.setup.log_filename)
        # update status
        self.status.update('s')
        # initialize bridge values
        bridge.load(self.setup.bridgefile)

        # initialize variables
        self.get_control_values()

        self.queue_msg("S")

        self.get_ip()

        self.eq3 = maxeq3.eq3data(self.setup.max_ip, 62910)
        self.eq3.read_data(True)
        # literal processing
        self._literal_process()

        self.export_csv("init")
        self.status.update('i')

    def queue_msg(self, msg):
        logmsg.update("Queqing [" + str(msg) + "]", 'D')
        self.var.msgQ.insert(0, msg)

    def _is_beta(self):
        return (bridge.try_read("beta", "no", False).upper() == "YES")


    def process_msg(self):
        """
        Process message queue
        :return: nothing
        """
        cw_msg = bridge.rcw("msg")
        while len(self.var.msgQ) > 0:
            logmsg.update("Message queue=" + str(self.var.msgQ), 'D')
            while not str(bridge.get(cw_msg)) == "":
                time.sleep(self.setup.timeout)
                tosend = self.var.msgQ.pop()
                logmsg.update("Sending message [" + str(tosend) + "]", 'D')
                if tosend == "E":
                    self.var.error = True
                    self.var.err2Clear = True
                elif tosend == "C":
                    self.var.err2Clear = False
                    self.var.err2LastStatus = True
                    logmsg.update("Clearing error LED", 'D')
                elif tosend == "R":
                    bridge.save(self.setup.bridgefile)
                if self.setup.target == "yun":
                    bridge.put(cw_msg, tosend)
                elif self.setup.target == "rpi":
                    if tosend == "H":
                        # action.do(True)
                        pass
                    elif tosend == "S":
                        # action.do(False)
                        pass

    def export_csv(self, cmd="init"):
        csv_file = self.setup.csv_log
        if cmd == "init":
            if os.path.exists(csv_file):
                os.rename(csv_file,
                          self.setup.place + self.setup.devname + "_" + time.strftime("%Y%m%d-%H%M%S",
                                                                                      time.localtime()) + ".csv")
            try:
                self.var.csv = open(csv_file, "a")
            except Exception:
                logmsg.update("Can't open CSV file: " + str(csv_file))
                raise
            else:
                # headers here
                self.var.csv.write(self.eq3.headers())
                self.var.csv.write("\r\n")
        elif cmd == "close":
            try:
                self.var.csv.close()
            except Exception:
                logmsg.update("Can't close CSV file!")

    def get_control_values(self):
        """ read control values from bridge """
        # try read preference settings, total or per
        self.setup.preference = bridge.try_read("pref", "per", True)
        # try read % valve for heat command
        self.setup.valve_switch = bridge.try_read("valve", 35, True)
        self.setup.svpnmw = bridge.try_read("svpnmw", 80, True)
        self.setup.total_switch = bridge.try_read("total", 150, True)
        # try get readMAX interval value, if not set it
        self.setup.intervals["max"][0] = bridge.try_read("int", 90, True)
        self.setup.intervals["slp"][0] = self.setup.intervals["max"][0] / self.setup.intervals["slp"][1]
        # try read num of valves to turn heat on
        self.setup.valve_num = bridge.try_read("valves", 1, True)
        # try read if autoupdate is OK
        self.setup.au = bridge.try_read("au", True, True)
        # try read how many minutes you can ignore valve after closing window
        self.eq3.ignore_time = bridge.try_read("ign_op", 30, True)
        # and if open windows warning is disabled, 0 = enables, 1 = disabled
        self.setup.no_oww = bridge.try_read("no_oww", 0, True)

    # check if its right time to update
    def _is(self, selector):
        tm = time.time()
        if tm > self.setup.intervals[selector][2]:
            self.setup.intervals[selector][2] = tm + self.setup.intervals[selector][0]
            return True
        else:
            return False

    def _getcmd(self):
        cmd_cw = bridge.rcw("cmd")
        localcmd = bridge.get(cmd_cw)
        if localcmd is None:
            return ""
        elif len(localcmd) > 0:
            bridge.put(cmd_cw, "")
        return localcmd

    def _isWinOpenTooLong(self, key):
        """
        Returns true if window is open longer that defined (setup.intervals["oww"][0]) time
        :param key: key
        :return: boolean
        """
        """ return True if window open time is > defined warning interval """
        v = self.eq3.devices[key]
        if self.eq3.isWinOpen(key):
            tmp = (datetime.datetime.now() - v[5]).total_seconds()
            if tmp > self.setup.intervals["oww"][0]:
                return True
            else:
                return False

    def _do_heat(self, state):
        if state:
            self.var.ht["total"][1] = time.time()
            self.queue_msg("H")
            if self.var.ventilating:
                self.status.update("hv")
            else:
                self.status.update("h")
        else:
            self.queue_msg("S")
            if self.var.ventilating:
                self.status.update("iv")
            else:
                self.status.update("i")
        # updateCounters(state)
        self.var.heating = state

    def control(self):
        tmp = {}
        open_windows = []
        for k, v in self.eq3.devices.iteritems():
            if v[4] == 2:
                room_id = str(v[3])
                room_name = str(self.eq3.rooms[room_id][0])
                tmp.update({k: room_name})

            if self._isWinOpenTooLong(k):
                open_windows.append(k)
                logmsg.update("Warning condition for window " + str(k) + " met")
            if self.eq3.isBattError(k):
                # send_warning("battery", k, "")
                pass
            if self.eq3.isRadioError(k):
                # send_warning("error", k, "")
                pass

        # check if ventilate and if not then send warning
        if not self.setup.no_oww and len(open_windows) < self.setup.ventilate_num:
            for idx, k in enumerate(open_windows):
                # send_warning("window", k, "")
                pass
        # else check if ventilating and update status
        else:
            if len(open_windows) >= self.setup.ventilate_num:
                self.var.ventilating = True
            else:
                self.var.ventilating = False

        # second web
        # secWebFile("owl", tmp)

        if self.var.err2Clear and not self.var.error:
            self.queue_msg("C")
        if self.var.err2LastStatus:
            self.var.err2LastStatus = False
            if self.var.heating:
                self.queue_msg("H")
                logmsg.update("Resuming heating state on status LED")

        # and now showtime
        # heat: 0 = disable, 1 = heat per, 2 = total, 3 = svpnmw
        heat = 0
        grt = 0
        valve_count = 0
        heat_valve = {}

        for k, v in self.eq3.valves.iteritems():
            # if valve is ok to evaluate
            if self.eq3.countValve(k):
                # if preference is per valve
                if self.setup.preference == "per":
                    # and valve position is over single valve position no matter what
                    if v[0] > self.setup.svpnmw:
                        heat = 3
                    # or valve is over desired position to switch heating on
                    elif v[0] > self.setup.valve_switch:
                        valve_count += 1
                        if valve_count >= self.setup.valve_num:
                            heat = 1
                            heat_valve.update(self.eq3.getKeyName(k))
                elif self.setup.preference == "total":
                    grt += v[0]
                    if grt >= self.setup.total_switch:
                        heat = 2

        # increment number of readings with heat on
        if heat:
            self.var.heatReadings += 1

        if bool(heat) != self.var.heating:
            if heat > 0:
                txt = "heating started due to"
                if heat == 1 and valve_count >= self.setup.valve_num:
                    for k, v in heat_valve.iteritems():
                        txt += " room " + str(v[0]) + ", valve " + str(v[1]) + "@" + str(v[2])
                elif heat == 2:
                    txt += " sum of valve positions = " + str(grt)
                elif heat == 3:
                    txt += " single valve position, no matter what " + str(self.setup.svpnmw) + "%"
                logmsg.update(txt)
                if bridge.try_read("mode", "auto", True).upper() == "AUTO":
                    self._do_heat(True)
            else:
                logmsg.update("heating stopped.")
                if bridge.try_read("mode", "auto", True).upper() == "AUTO":
                    self._do_heat(False)

    def intervals(self):
        # do upgrade according schedule
        if self._is("upg"):
            if not autoupdate.do(self.setup.version, self._is_beta()):
                logmsg.update("Auto update is disabled or failed.")
            else:
                logmsg.update("thermeq3 updated.")
                body = ("<h1>Device upgrade information.</h1>\n"
                        "   <p>Hello, I'm your thermostat and I have a news for you.<br/>\n"
                        "	Please take a note, that I found new version of thermeq3 app<br/>\n"
                        "   and I'll be upgraded in few seconds.</br>\n"
                        "	Resistance is futile :).<br/>")
                # sendWarning("upgrade", temp_key, body)
        # do update variables according schedule
        if self._is("var"):
            # >>> updateAllTimes()
            bridge.save(self.setup.bridgefile)
            self.get_ip()
            self.update_ignores_2sit()
        # check max according schedule
        if self._is("max"):
            # beta features here
            if self._is_beta():
                sm, am, kk = profiles.do(self.setup.selectedMode, self.var.actModeIndex, self.var.situation)
                if sm != self.setup.selectedMode or am != self.var.actModeIndex:
                    self.setup.selectedMode = sm
                    self.var.actModeIndex = am
                    self.set_mode(kk)
            # end of beta
            cmd = self._getcmd()
            if cmd == "quit":
                return 0xFF
            elif cmd == "log_debug":
                logmsg.level('D')
            elif cmd == "log_info":
                logmsg.level('I')
            elif cmd[0:4] == "mute":
                key = cmd[4:]
                if key in self.eq3.windows:
                    self.eq3.windows[key][0] = datetime.datetime.now()
                    self.eq3.windows[key][1] = True
                    logmsg.update("OWW for key " + str(key) + " is muted for " + str(
                        self.setup.intervals["oww"][2]) + " seconds.")
            elif cmd == "rebridge":
                bridge.load(self.setup.bridgefile)
                # literal processing
                self._literal_process()
            elif cmd == "updatetime":
                # updateAllTimes()
                pass
            elif cmd == "led":
                if self.var.heating:
                    self.queue_msg("H")
                else:
                    self.queue_msg("S")
            elif cmd == "upgrade":
                # doUpdate()
                pass
            if self.eq3.read_data(False):
                logmsg.update(self._status_msg())
                logmsg.update(self.eq3.plain(), 'I')
                # update JSONs
                self.get_control_values()
                self.control()
                # doDevLogging()
                pass

    def _status_msg(self):
        """
        Return formatted status string
        :return: string
        """
        logstr = self.status.actual + ", "
        if self.setup.preference == "per":
            logstr += str(self.setup.valve_switch) + "%" + " at " + str(self.setup.valve_num) + " valve(s)."
        elif self.setup.preference == "total":
            logstr += "total value of " + str(self.setup.total_switch) + "."
        return logstr

    def _get_uptime(self):
        if os.name != "nt":
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                return str(datetime.timedelta(seconds=uptime_seconds)).split(".")[0]
        else:
            uptime = os.popen('systeminfo', 'r')
            data = uptime.readlines()
            uptime.close()
            return str(0)

    def update_uptime(self):
        tmp = time.time()
        bridge.put("uptime", self._get_uptime())
        bridge.put("appuptime", datetime.timedelta(seconds=int(tmp - self.var.appStartTime)))

    def update_all(self):
        self.update_uptime()
        self.update_counters(False)

    def update_counters(self, heat_start):
        # save the date
        nw = datetime.datetime.date(datetime.datetime.now()).strftime("%d-%m-%Y")
        tm = time.time()

        # update total heat counter
        if self.var.heating:
            tmp = self.var.ht["total"][0]
            tmp += int(time.time() - self.var.ht["total"][1])
            bridge.put("ht", self.var.ht)
            bridge.put("htstr", datetime.timedelta(seconds=tmp))
            logmsg.update("Total heat counter updated to " + str(datetime.timedelta(seconds=tmp)))
            self.var.ht["total"][0] = tmp
            self.var.ht["total"][1] = time.time()

        # is there a key for today?
        if nw in self.var.ht:
            if heat_start:
                self.var.ht[nw][1] = tm
            elif self.var.heating:
                totalheat = int(self.var.ht[nw][0] + (tm - self.var.ht[nw][1]))
                self.var.ht[nw] = [totalheat, time.time()]
                bridge.put("ht", self.var.ht)
                bridge.put("daily", datetime.timedelta(seconds=totalheat))
        else:
            if len(self.var.ht) > 1:
                # if there a key, this must be old key(s)
                # save the old date, and flush values into log
                for k in self.var.ht.keys():
                    v = self.var.ht[k]
                    if not k == "total":
                        logmsg.update(str(k) + " heating daily summary: " + str(datetime.timedelta(seconds=v[0])), 'I')
                        logmsg.update("Deleting old daily key: " + str(k), 'D')
                        del self.var.ht[k]
                # and close CSV file
                self.export_csv("close")
            # create the new key
            logmsg.update("Creating new daily key: " + str(nw))
            self.var.ht.update({nw: [0, time.time()]})
            # so its a new day, update other values
            self.export_csv("init")
            # day readings warning, take number of heated readings and divide by 2
            drw = self.var.heatReadings / 2
            logmsg.update("Day reading warnings value=" + str(drw))
            for k, v in self.var.dev_log.iteritems():
                logmsg.update("Valve: " + str(k) + " has value " + str(v[0]))
                if v[0] > drw:
                    logmsg.update("Valve: " + str(k) +
                                  " reports during heating too many same % positions, e.g. " +
                                  str(v[0]) + " per " + str(drw))
                self.var.dev_log[k][0] = 0
            self.var.heatReadings = 0
            bridge.save(self.setup.bridgefile)

    def _literal_process(self):
        for k, v in bridge.cw.iteritems():
            if v[2]:
                tmp = bridge.get(k)
                codeword = v[0]
                setvalue = v[1]
                try:
                    lit_result = literal_eval(tmp)
                except Exception:
                    logmsg.update("Bridge error codeword [" + str(codeword) + "] value [" + str(setvalue) + "]", 'D')
                else:
                    if codeword == bridge.rcw("ht"):
                        self.var.ht = lit_result
                    elif codeword == bridge.rcw("ign"):
                        self.eq3.ignored_valves = lit_result

    def update_ignores_2sit(self):
        self.var.situation = weather.weather_for_woeid(self.setup.location)
        temp = int(self.var.situation["current_temp"])

        # modify OWW
        tmr = weather.interval_scale(temp, (-35.0, 35.0), (0, 10), (10, 360), True)
        self.setup.intervals["oww"] = [tmr * 60, (3 * tmr) * 60, (3 * tmr) * 60]
        logmsg.update("OWW interval updated to " + str(self.setup.intervals["oww"]))

        # and now modify valve ignore time
        tmr = weather.interval_scale(temp, (0.0, 35.0), (1.7, 3.0), (15, 120), False)
        self.var.ignore_time = self.setup.window_ignore_time + tmr
        bridge.put("ign_op", self.var.ignore_time)
        logmsg.update("Valve ignore interval updated to " + str(self.var.ignore_time), 'D')

    def set_mode(self, value):
        if value[3] == "total":
            self.setup.total_switch = value[2]
        else:
            self.setup.valve_switch = value[2]
        self.setup.preference = value[3]
        self.setup.intervals["max"][0] = value[4]
        self.setup.valve_num = value[5]
        # just sleep value, always calculated as max[0] / slp[1]
        self.setup.intervals["slp"][0] = int(value[4] / self.setup.intervals["slp"][1])
        bridge.put("int", self.setup.intervals["max"][0])

    def get_ip(self):
        """
        Get IP and set variables
        :return: nothing
        """
        tmp = public_ip.get()
        if tmp == 0xFF:
            logmsg.update("Error getting IP address from hostname, please check resolv.conf or hosts or both!", 'E')
        else:
            self.setup.myip = tmp
            if public_ip.is_private(tmp):
                logstr = "Local"
            else:
                logstr = "Public"
            logmsg.update(logstr + " IP address: " + self.setup.myip)

    # some warnings
    def send_warning(self, selector, dev_key, body_txt):
        subject = ""
        body = ""
        d = self.eq3.devices[dev_key]
        dn = d[2]
        r = d[3]
        rn = self.eq3.rooms[str(r)]
        sil = self.silence(dev_key, selector == "window")
        if sil == 1:
            logmsg.update("Warning for device " + str(dev_key) + " is muted!")
            return
        mutestr = "http://" + self.setup.myip + ":" + str(self.setup.extport) + "/data/put/command/mute" + str(dev_key)
        if selector == "window":
            owd = int((datetime.datetime.now() - self.eq3.devices[dev_key][5]).total_seconds())
            oww = int((datetime.datetime.now() - self.eq3.windows[dev_key][0]).total_seconds())
            if sil == 0 and oww < self.setup.intervals["oww"][1]:
                return
            subject = "Open window in room " + str(rn[0]) + ". Warning from thermeq3 device"
            body = """<h1>Device %(a0)s warning.</h1>
            <p>Hello, I'm your thermostat and I have a warning for you.<br/>
            Please take a care of window <b>%(a0)s</b> in room <b>%(a1)s</b>.
            Window in this room is now opened more than <b>%(a2)d</b> mins.<br/>
            Threshold for warning is <b>%(a3)d</b> mins.<br/>
            </p><p>You can <a href="%(a4)s">mute this warning</a> for %(a5)s mins.""" % \
                   {'a0': str(dn),
                    'a1': str(rn[0]),
                    'a2': int(owd / 60),
                    'a3': int(self.setup.intervals["oww"][0] / 60),
                    'a4': str(mutestr),
                    'a5': int(self.setup.intervals["oww"][2] / 60)}
        else:
            if sil == 0 and not self._is("wrn"):
                return
            if selector == "battery":
                subject = "Battery status for device " + str(dn) + ". Warning from thermeq3 device"
                body = """<h1>Device %(a0)s battery status warning.</h1>
                <p>Hello, I'm your thermostat and I have a warning for you.<br/>
                Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
                This device have low batteries, please replace batteries.<br/>
                </p><p>You can <a href="%(a2)s">mute this warning</a> for %(a3)s mins.""" % \
                       {'a0': str(dn),
                        'a1': str(rn[0]),
                        'a2': str(mutestr),
                        'a3': int(self.setup.intervals["wrn"][1] / 60)}
            elif selector == "error":
                subject = "Error report for device " + str(dn) + ". Warning from thermeq3 device"
                body = """<h1>Device %(a0)s radio error.</h1>
                <p>Hello, I'm your thermostat and I have a warning for you.<br/>
                Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
                This device reports error.<br/>
                </p><p>You can <a href="%(a2)s">mute this warning</a> for %(a3)s mins.""" % \
                       {'a0': str(dn),
                        'a1': str(rn[0]),
                        'a2': str(mutestr),
                        'a3': int(self.setup.intervals["wrn"][1] / 60)}
            elif selector == "openmax":
                subject = "Can't connect to MAX! Cube! Warning from thermeq3 device"
                body = body_txt
            elif selector == "upgrade":
                subject = "thermeq3 device is going to be upgraded"
                body = body_txt

        m_id = self.setup.get_mail_data()
        m_id.update({"s": subject})
        msg = mailer.compose(m_id, body)

        if mailer.send_email(m_id, msg.as_string()) == 0 and selector == "window":
            self.eq3.windows[dev_key][0] = datetime.datetime.now()

    def silence(self, key, is_win):
        #
        # d_w = key: OW_time(thisnow), isMuted(False), warning/error count(0)
        #
        # is there key in dict?
        dt = datetime.datetime.now()
        if key not in self.eq3.windows:
            # there no key, so its new warning
            logmsg.update("No key " + str(key) + " in windows. Key added.")
            if is_win:
                self.eq3.windows.update({key: [self.eq3.devices[key][5], False, 0]})
            else:
                self.eq3.windows.update({key: [dt, False, 0]})
            return 2
        else:
            # yes, there it is, so check if we are silent, if so exit, otherwise reset mute
            # threshold, send every X, muted for X
            # "oww": [10*60, 30*60, 45*60]
            # threshold, muted for X, time.time()
            # "wrn": [60*60, 60*60, tm]
            if self.eq3.windows[key][1]:
                # yes, we must be silent
                if is_win:
                    tmp = self.eq3.windows[key][0] + datetime.timedelta(seconds=self.setup.intervals["oww"][2])
                else:
                    tmp = self.eq3.windows[key][0] + datetime.timedelta(seconds=self.setup.intervals["wrn"][1])
                if tmp < dt:
                    return 1
                else:
                    # silence is over
                    self.eq3.windows[key][1] = False

        # increment warning counter for this key
        self.eq3.windows[key][2] += 1
        if self.eq3.windows[key][2] > self.setup.abnormalCount:
            logmsg.update(
                "Abnormal #warnings for device [" + str(key) + "], name [" + str(self.eq3.devices[key][2]) + "]")
            self.eq3.windows[key][2] = 0
        return 0
