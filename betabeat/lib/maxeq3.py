"""
EQ-3/ELV MAX! communication
"""
# imports
import logmsg
import socket
import time
import traceback
import base64
import datetime
import json


class eq3data:
    def __init__(self, ip_address, port):
        self.max_ip = ip_address
        self.max_port = port
        self.timeout = 10
        #
        # dictionaries and lists
        #
        self.maxid = {"sn": "000000", "rf": "", "fw": ""}
        self.valves = {}
        self.rooms = {}
        self.devices = {}
        # opened windows
        self.windows = {}
        # ignored valves
        self.ignored_valves = {}
        # to save Exception and e values
        self.return_error = []
        # logger messages queue
        self.log_messages = []
        #
        # variables
        #
        # how many minutes after closing window is valve ignored
        self.ignore_time = 0
        # communication errors count
        self.comm_error = 0
        # how many times try connect to MAX!Cube
        self.max_iteration = 3

    def getName(self, k):
        """ return complete names for valve, room """
        v = self.valves[k]
        dn = self.devices[k][2]
        rn = self.rooms[str(self.devices[k][3])][0]
        return [rn, dn, v]

    def getKeyName(self, k):
        """ return complete names for valve, room as dictionary """
        return {k: self.getName(k)}

    def isRadioError(self, key):
        """ True if radio error on device with key """
        v = self.devices[key]
        if v[6] & 8 == 8:
            return True
        else:
            return False

    def isBattError(self, key):
        """ True if battery error on device with key """
        v = self.devices[key]
        if v[7] & 128 == 128:
            return True
        else:
            return False

    def isWinOpen(self, key):
        """ Return true if window is open """
        v = self.devices[key]
        if v[0] == 4 and v[4] == 2:
            return True
        else:
            return False

    def countValve(self, key):
        """ return True if valve is NOT ignored """
        if key in self.ignored_valves:
            if self.ignored_valves[key] < time.time():
                del self.ignored_valves[key]
            else:
                return False
        return True

    def _hexify(self, tmpadr):
        """ returns hexified address """
        return "".join("%02x" % ord(c) for c in tmpadr).upper()

    def _incError(self):
        """ increment error variable """
        self.comm_error += 1

    def _readlines(self, sock, recv_buffer=4096, delim="\r\n"):
        buffer = ""
        data = True
        while data:
            try:
                data = sock.recv(recv_buffer)
                buffer += data
                while buffer.find(delim) != -1:
                    line, buffer = buffer.split("\n", 1)
                    yield line
            except socket.timeout:
                return
        return

    def _setIgnoredValves(self, key):
        room = self.devices[key][3]
        for k, v in self.devices.iteritems():
            # this is heating thermostat and is in room where we want ignore all heating thermostats
            # and is not in d_ignore dictionary = is not ignored now
            if v[0] == 1 and v[3] == room and k not in self.ignored_valves:
                # don't heat X*60 seconds after closing window
                self.ignored_valves.update({k: time.time() + self.ignore_time * 60})
                logmsg.update("Ignoring valve " + str(k) + " until " + time.strftime("%d/%m/%Y %H:%M:%S",
                                                                                     time.localtime(
                                                                                         self.ignored_valves[k])), 'D')

    def open(self):
        """ open communication to MAX! Cube """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # on some system use code below:
        # self.client_socket.setblocking(0)
        self.client_socket.settimeout(int(self.timeout / 2))

        self.max_iteration = 3
        _i = 0
        _result = False
        while _i < self.max_iteration:
            try:
                self.client_socket.connect((self.max_ip, self.max_port))
            except Exception, e:
                self._incError()
                _i += 1
                # wait predefined time
                time.sleep(int(self.timeout / self.max_iteration))
                self.return_error = [Exception, e, str(traceback.format_exc())]
            else:
                _i = self.max_iteration
                _result = True
        # return result, if False then return_error contains error
        return _result

    def close(self):
        """ close connection to MAX """
        self.client_socket.close()

    def readData(self, refresh=False):
        if self.open():
            self.read(refresh)
        # close session
        self.close()

    def read(self, refresh):
        """ read data from MAX! cube """
        self.client_socket.settimeout(int(self.timeout / 3))
        for line in self._readlines(self.client_socket):
            data = line
            sd = data[2:].split(",")
            if data[0] == 'H':
                self.maxCmd_H(sd)
            elif data[0] == 'M':
                self.maxCmd_M(sd, refresh)
            elif data[0] == 'C':
                self.maxCmd_C(sd)
            elif data[0] == 'L':
                self.maxCmd_L(sd)

    def maxCmd_H(self, line):
        """ process H response """
        self.maxid["sn"] = line[0]
        self.maxid["rf"] = line[1]
        self.maxid["fw"] = line[2]

    def maxCmd_M(self, line, refresh):
        """ process M response """
        es = base64.b64decode(line[2])
        room_num = ord(es[2])
        es_pos = 3
        this_now = datetime.datetime.now()
        for _ in range(0, room_num):
            room_id = str(ord(es[es_pos]))
            room_len = ord(es[es_pos + 1])
            es_pos += 2
            room_name = es[es_pos:es_pos + room_len]
            es_pos += room_len
            room_adr = es[es_pos:es_pos + 3]
            es_pos += 3
            if room_id not in self.rooms or refresh:
                #										id   :	0room_name, 1room_address,   2is_win_open, 3curr_temp
                self.rooms.update({room_id: [room_name, self._hexify(room_adr), False, 99.99]})
        dev_num = ord(es[es_pos])
        es_pos += 1
        for _ in range(0, dev_num):
            dev_type = ord(es[es_pos])
            es_pos += 1
            dev_adr = self._hexify(es[es_pos:es_pos + 3])
            es_pos += 3
            dev_sn = es[es_pos:es_pos + 10]
            es_pos += 10
            dev_len = ord(es[es_pos])
            es_pos += 1
            dev_name = es[es_pos:es_pos + dev_len]
            es_pos += dev_len
            dev_room = ord(es[es_pos])
            es_pos += 1
            if dev_adr not in self.devices or refresh:
                #                            0type     1serial 2name     3room    4OW,5OW_time, 6status, 7info, 8temp offset
                self.devices.update({dev_adr: [dev_type, dev_sn, dev_name, dev_room, 0, this_now, 0, 0, 7]})

    def maxCmd_C(self, line):
        """ process C response """
        es = base64.b64decode(line[1])
        if ord(es[0x04]) == 1:
            dev_adr = self._hexify(es[0x01:0x04])
            self.devices[dev_adr][8] = es[0x16]

    def maxCmd_L(self, line):
        """ process L response """
        es = base64.b64decode(line[0])
        es_pos = 0
        while es_pos < len(es):
            dev_len = ord(es[es_pos]) + 1
            valve_adr = self._hexify(es[es_pos + 1:es_pos + 4])
            valve_status = ord(es[es_pos + 0x05])
            valve_info = ord(es[es_pos + 0x06])
            valve_temp = 0xFF
            valve_curtemp = 0xFF
            # WallMountedThermostat (dev_type 3)
            if dev_len == 13:
                if valve_info & 3 != 2:
                    # get set temp
                    valve_temp = float(int(self._hexify(es[es_pos + 0x08]), 16)) / 2
                    # get measured temp
                    valve_curtemp = float(int(self._hexify(es[es_pos + 0x0C]), 16)) / 10
                    # extract room name from this WallMountedThermostat
                    wall_room_id = str(self.devices[valve_adr][3])
                    # and update its value to current temperature as read from WallMountedthermostat
                    self.rooms[wall_room_id][3] = valve_curtemp
                    # HeatingThermostat (dev_type 1 or 2)
            elif dev_len == 12:
                valve_pos = ord(es[es_pos + 0x07])
                if valve_info & 3 != 2:
                    # get set temp
                    valve_temp = float(int(self._hexify(es[es_pos + 0x08]), 16)) / 2
                    # extract room name from this HeatingThermostat
                    valve_room_id = str(self.devices[valve_adr][3])
                    # if room temp not set i.e. still returning default 99.99
                    if self.rooms[valve_room_id][3] == 99.99:
                        # get room temp from this valve
                        valve_curtemp = float(ord(es[es_pos + 0x0A])) / 10
                        # and update room temp too
                        self.rooms[valve_room_id][3] = valve_curtemp
                    else:
                        # read room temp which was earlier set by wall thermostat
                        valve_curtemp = self.rooms[valve_room_id][3]
                self.valves.update({valve_adr: [valve_pos, valve_temp, valve_curtemp]})
            # WindowContact
            elif dev_len == 7:
                tmp_open = ord(es[es_pos + 0x06]) & 2
                if tmp_open != self.devices[valve_adr][4]:
                    tmp_txt = "Window contact " + str(self.devices[valve_adr][2]) + " is now "
                    r_id = str(self.devices[valve_adr][3])
                    if tmp_open == 0:
                        logmsg.update(tmp_txt + "closed.", 'D')
                        self.rooms[r_id][2] = False
                        if valve_adr in self.windows:
                            logmsg.update("Key " + str(valve_adr) + " in windows deleted.", 'D')
                            del self.windows[valve_adr]
                        # now check for window closed ignore interval, if non zero set valves to ignore
                        if self.ignore_time > 0:
                            self._setIgnoredValves(valve_adr)
                    else:
                        logmsg.update(tmp_txt + "opened.", 'D')
                        self.rooms[r_id][2] = True
                    self.devices[valve_adr][4] = tmp_open
                    self.devices[valve_adr][5] = datetime.datetime.now()
            # save status and info
            self.devices[valve_adr][6] = valve_status
            self.devices[valve_adr][7] = valve_info
            es_pos += dev_len

    def csv(self):
        """ format csv string, the second part, just valves """
        tmp = ""
        for k, v in self.valves.iteritems():
            tmp += str(v[0]) + "," + str(v[1]) + "," + str(v[2]) + ","
        return tmp

    def plain(self):
        rooms = {}
        for k, v in self.rooms.iteritems():
            rooms.update({str(v[0]): ["", v[2]]})

        for k, v in self.valves.iteritems():
            # update rooms string
            room_id = str(self.getName(k)[0])
            roomStr = rooms[room_id][0]
            roomStr += "\r\n\t[" + str(k) + "] " + '{:<20}'.format(str(self.devices[k][2])) + "@" + '{:>3}'.format(
                str(v[0])) + "% @ " + \
                       '{:>4}'.format(str(v[1])) + "'C # " + '{:>4}'.format(str(v[2])) + "'C "
            cv = self.countValve(k)
            if cv:
                roomStr += "(+)"
            else:
                roomStr += "(-)"

            rooms[room_id][0] = roomStr

        logstr = "Actual positions:"
        for k, v in rooms.iteritems():
            logstr += "\r\nRoom: " + str(k)
            if v[1]:
                logstr += ", window opened"
        logstr += str(v[0])

        return logstr

    def json_status(self):
        current = {}
        for k, v in self.rooms.iteritems():
            current.update({str(v[0]): {}})

        for k, v in self.valves.iteritems():
            room_id = str(self.getName(k)[0])
            cv = self.countValve(k)
            current[room_id].update(
                {str(k): [str(self.devices[k][2]), str(v[0]), str(v[1]), str(v[2]), str(1 if cv else 0)]})

        return str(current)

    def nice(self):
        tmpstr = self.plain()
        tmpstr.replace("\r\n", "<br/>")
        tmpstr.replace("\t", "&#9;")
        return "<html>\r\n<title>\r\nStatus</title>\r\n<body>\r\n<p><pre>" + tmpstr + "</pre></p>\r\n</body>\r\n</html>"

    def headers(self, rn_vn = False):
        tmp = ""
        for k, v in self.valves.iteritems():
            if rn_vn:
                room_id = str(self.getName(k)[0])
                name = self.rooms[room_id][0] + "-" + self.devices[k][2]
            else:
                name = self.devices[k][2]
            tmp += name + "," + name + "," + name + ","

        return tmp[:-1]

    def rooms_status_id(self):
        #rooms = id : room_name, room_address, is_win_open, curr_temp
        tmp = {}
        for k, v in self.rooms.iteritems():
            tmp.update({v[1]: [v[0], v[2], v[3]]})
        return json.dumps(tmp)

    def rooms_status_name(self):
        #rooms = id : room_name, room_address, is_win_open, curr_temp
        tmp = {}
        for k, v in self.rooms.iteritems():
            tmp.update({v[0]: [v[1], v[2], v[3]]})
        return json.dumps(tmp)
