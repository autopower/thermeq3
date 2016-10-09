"""
EQ-3/ELV MAX! communication
"""
# imports
import socket
import time
import traceback
import base64
import datetime
import json

"""
new devices dictionary
devices = {
    address: {
        type: string,
        serial: string,
        name: string,
            if type=1 then {pos: int, temp: float, c_temp: float}
            if type=4 then {open: boolean, ow_time: datetime}
        status: [status, info],
        other: [temp_offset]
        }
    }
"""


class EQ3Data:
    def __init__(self, ip_address, port):
        self.max_ip = ip_address
        self.max_port = port
        self.timeout = 10
        #
        # dictionaries and lists
        #
        self.maxid = {"sn": "000000", "rf": "", "fw": ""}
        # valves = {devices-addr: [0/valve_pos, 1/valve_temp, 2/valve_curtemp, 3/valve_name]}
        self.valves = {}
        # rooms = {id : [0/room_name, 1/room_address, 2/is_win_open, 3/curr_temp, 4/average valve position]}
        self.rooms = {}
        # devices = {address: [0/type, 1/serial, 2/name, 3/room:id, 4/OW, 5/OW_time, 6/status, 7/info, 8/temp offset]}
        self.devices = {}
        # device log, used to monitor valve positions, if many same positions than probably error
        self.device_log = {}
        # opened windows = {key: OW_time(now), isMuted(False), warning/error count(0)}
        self.windows = {}
        # ignored valves
        self.ignored_valves = {}
        # to save Exception and e values
        self.return_error = []
        # logger messages queue
        self.log_messages = []
        # how many minutes after closing window is valve ignored
        self.ignore_time = 0
        # communication errors count
        self.comm_error = 0
        # how many times try connect to MAX!Cube
        self.max_iteration = 3
        # outside init declaration
        self.client_socket = None
        # set zero temp from HT or not
        self.set_zero = True

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def is_same(self, key, error_interval=2):
        """
        Problem prediction routine, if during heating valve didn't change position, something is wrong
        :param key: string, key
        :param error_interval: integer, plus/minus value
        :return: boolean
        """
        tmp = self.device_log[key][1]
        kv = self.valves[key][1]
        if tmp - error_interval <= kv <= tmp + error_interval:
            return True
        else:
            return False

    def get_full_name(self, k):
        """
        Return complete names for valve, room
        :param k: key
        :return: list [room name, device name, valve list]
        """
        v = self.valves[k]
        dn = self.devices[k][2]
        rn = self.rooms[str(self.devices[k][3])][0]
        return [rn, dn, v]

    def get_key_full_name(self, k):
        """
        Return complete names for valve, room as dictionary
        :param k: key
        :return: dictionary {key: [room name, device name, valve list for key]}
        """
        return {k: self.get_full_name(k)}

    def device_name(self, k):
        """
        Return device name
        :param k: key
        :return: valve name/string
        # devices = {addr: [type, serial, name, room, OW, OW_time, status, info, temp offset]}
        """
        dn = str(self.devices[k][2])
        return dn

    def get_room_name(self, k):
        """
        Return device room name for device key/address
        :param k:
        :return: room name/string
        """
        rn = self.rooms[str(self.devices[k][3])][0]
        return rn

    def is_valid(self, valve_info):
        """
        :param valve_info: valve status info
        :return: boolean, true if valid
        """
        return bool((valve_info & 0b00010000) >> 4)

    def is_radio_error(self, key):
        """
        True if radio error on device with key
        :param key: key
        :return: Boolean
        """
        v = self.devices[key]
        if v[6] & 8 == 8:
            return True
        else:
            return False

    def is_battery_error(self, key):
        """
        True if battery error on device with key
        :param key: key
        :return: boolean
        """
        """ True if battery error on device with key """
        v = self.devices[key]
        if v[7] & 128 == 128:
            return True
        else:
            return False

    def is_window_open(self, key):
        """
        Return true if window is open
        :param key: key
        :return: boolean
        """
        v = self.devices[key]
        if v[0] == 4 and v[4] == 2:
            return True
        else:
            return False

    def count_valve(self, key):
        """
        Return True if valve is NOT ignored
        :param key: key
        :return: boolean
        """
        if key in self.ignored_valves:
            if self.ignored_valves[key] < time.time():
                del self.ignored_valves[key]
            else:
                return False
        return True

    def _hexify(self, addr):
        """
        Returns hexified address
        :param addr: string, device address
        :return: string
        """
        return "".join("%02x" % ord(c) for c in addr).upper()

    def _inc_error(self):
        """
        Increment error variable
        :return: nothing
        """
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

    def _set_ignored_valves(self, key):
        room = self.devices[key][3]
        for k, v in self.devices.iteritems():
            # this is heating thermostat and is in room where we want ignore all heating thermostats
            # and is not in ignored_valves dictionary = is not ignored now
            if v[0] == 1 and v[3] == room and k not in self.ignored_valves:
                # don't heat X*60 seconds after closing window
                self.ignored_valves.update({k: time.time() + self.ignore_time * 60})

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
                self._inc_error()
                _i += 1
                # wait predefined time
                time.sleep(int(self.timeout / self.max_iteration))
                self.return_error.append([Exception, e, str(traceback.format_exc())])
            else:
                _i = self.max_iteration
                _result = True
        # return result, if False then return_error contains error
        return _result

    def close(self):
        """ close connection to MAX """
        self.client_socket.close()

    def _process(self):
        """
        Update room average valve position
        :return: nothing
        """
        tmp_room = {}
        for k, v in self.valves.iteritems():
            room_id = self.get_room_name(k)
            if self.count_valve(k):
                if room_id not in tmp_room:
                    position = 0
                    count = 1
                else:
                    position = tmp_room[room_id][0]
                    count = tmp_room[room_id][1] + 1
                tmp_room.update({room_id: [position + v[0], count]})

        # erase rooms average valve position
        for k, v in self.rooms.iteritems():
            self.rooms[k][4] = 0
        # set rooms average valve position
        for k, v in tmp_room.iteritems():
            try:
                result = v[0] / v[1]
            except:
                result = 0
            finally:
                r_id = self.get_room_id_by_name(k)
                if k is not None:
                    self.rooms[r_id][4] = result

    def get_room_id_by_name(self, r_name):
        for k, v in self.rooms.iteritems():
            if v[0] == r_name:
                return k
        return None

    def read_data(self, refresh=False):
        """
        :param refresh: passable argument
        :return: boolean, list
        """
        result = False
        if self.open():
            self.read(refresh)
            self._process()
            result = True
        # close session
        self.close()
        return result, self.return_error

    def read(self, refresh):
        """
        read data from MAX! cube
        :param refresh: boolean
        :return: nothing
        """
        self.client_socket.settimeout(int(self.timeout / 3))
        for line in self._readlines(self.client_socket):
            data = line
            sd = data[2:].split(",")
            if data[0] == 'H':
                self.cmd_h(sd)
            elif data[0] == 'M':
                self.cmd_m(sd, refresh)
            elif data[0] == 'C':
                self.cmd_c(sd)
            elif data[0] == 'L':
                self.cmd_l(sd)

    def cmd_h(self, line):
        """
        Process H response
        :param line: string
        :return: nothing
        """
        self.maxid["sn"] = line[0]
        self.maxid["rf"] = line[1]
        self.maxid["fw"] = line[2]

    def cmd_m(self, line, refresh):
        """
        Process H response
        :param line: string
        :param refresh: boolean
        :return:
        """
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
                # id  :	0room_name, 1room_address,   2is_win_open, 3curr_temp
                self.rooms.update({room_id: [room_name, self._hexify(room_adr), False, 99.99, 0]})
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
                # 0type     1serial 2name     3room    4OW,5OW_time, 6status, 7info, 8temp offset
                self.devices.update({dev_adr: [dev_type, dev_sn, dev_name, dev_room, 0, this_now, 0, 0, 7]})

    def cmd_c(self, line):
        """
        process C response
        :param line: string
        :return: nothing
        """
        es = base64.b64decode(line[1])
        if ord(es[0x04]) == 1:
            dev_adr = self._hexify(es[0x01:0x04])
            self.devices[dev_adr][8] = es[0x16]

    def cmd_l(self, line):
        """
        process L response
        :param line: string
        :return: nothing
        """
        es = base64.b64decode(line[0])
        es_pos = 0
        while es_pos < len(es):
            dev_len = ord(es[es_pos])
            valve_adr = self._hexify(es[es_pos + 1:es_pos + 4])
            valve_status = ord(es[es_pos + 0x05])
            valve_info = ord(es[es_pos + 0x06])
            valve_temp = 0xFF
            valve_curr_temp = 0xFF
            # WallMountedThermostat (dev_type 3)
            if dev_len == 12:
                if self.is_valid(valve_info):
                    lsb = ord(es[es_pos + 0x08]) & 0b01111111
                    msb = ((ord(es[es_pos + 0x08]) & 0b10000000) >> 7) * 256
                    # get set temp
                    valve_temp = float(lsb) / 2
                    # get measured temp
                    lsb = ord(es[es_pos + 0x0C])
                    valve_curr_temp = float(msb + lsb) / 10
                    # extract room name from this WallMountedThermostat
                    wall_room_id = str(self.devices[valve_adr][3])
                    # and update its value to current temperature as read from WallMountedthermostat
                    self.rooms[wall_room_id][3] = valve_curr_temp
            # HeatingThermostat (dev_type 1 or 2)
            elif dev_len == 11:
                valve_pos = ord(es[es_pos + 0x07])
                if self.is_valid(valve_info):
                    lsb = ord(es[es_pos + 0x08]) & 0b01111111
                    msb = ((ord(es[es_pos + 0x08]) & 0b10000000) >> 7) * 256
                    # get set temp
                    valve_temp = float(lsb) / 2
                    # extract room name from this HeatingThermostat
                    valve_room_id = str(self.devices[valve_adr][3])
                    # if room temp not set i.e. still returning default 99.99
                    if self.rooms[valve_room_id][3] == 99.99:
                        # get room temp from this valve
                        lsb = ord(es[es_pos + 0x09])
                        valve_curr_temp = float(msb + lsb) / 10
                        # and update room temp too
                        self.rooms[valve_room_id][3] = valve_curr_temp
                    else:
                        # read room temp which was earlier set by wall thermostat
                        valve_curr_temp = self.rooms[valve_room_id][3]
                # check if current temperature is 0.0 and if set_zero is disabled, then get "obsolete actual" temp,
                # just to have no 0.0 in log or CSV
                if valve_curr_temp == 0.0 and not self.set_zero:
                    valve_curr_temp = self.valves[valve_adr][2]
                self.valves.update({valve_adr: [valve_pos, valve_temp, valve_curr_temp]})
            # WindowContact
            elif dev_len == 6:
                tmp_open = ord(es[es_pos + 0x06]) & 2
                # check if some this key is not remain of old installation, typically unpaired contact
                if valve_adr in self.devices:
                    # if state changed
                    if tmp_open != self.devices[valve_adr][4]:
                        # get room id
                        r_id = str(self.devices[valve_adr][3])
                        # if window is now closed
                        if tmp_open == 0:
                            self.rooms[r_id][2] = False
                            if valve_adr in self.windows:
                                del self.windows[valve_adr]
                            # check for window closed ignore interval, if non zero, set valves to ignore
                            if self.ignore_time > 0:
                                self._set_ignored_valves(valve_adr)
                        else:
                            # or is opened now
                            self.rooms[r_id][2] = True
                        self.devices[valve_adr][4] = tmp_open
                        self.devices[valve_adr][5] = datetime.datetime.now()
                else:
                    # some error logging
                    self.return_error.append(["Wrong address: " + str(valve_adr)])
            # save status and info
            self.devices[valve_adr][6] = valve_status
            self.devices[valve_adr][7] = valve_info
            es_pos += (dev_len + 1)

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
            room_id = str(self.get_full_name(k)[0])
            room_str = rooms[room_id][0]
            room_str += "\r\n\t[" + str(k) + "] " + '{:<20}'.format(str(self.devices[k][2])) + "@" + \
                        '{:>3}'.format(str(v[0])) + "% @ " + \
                        '{:>4}'.format(str(v[1])) + "'C # " + '{:>4}'.format(str(v[2])) + "'C "
            cv = self.count_valve(k)
            if cv:
                room_str += "(+)"
            else:
                room_str += "(-) till " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(self.ignored_valves[k]))

            rooms[room_id][0] = room_str

        logstr = "Actual positions:"
        for k, v in rooms.iteritems():
            logstr += "\r\nRoom: " + str(k)
            if v[1]:
                logstr += ", open window"
            logstr += str(v[0])

        return logstr

    def json_status(self):
        """
        Return json in format
            {room_name: {valve_addr: {valve_name, valve_position, set_temp, current_temp, count_valve, ignore_until}}}
        :return: json
        """
        # devices = {addr: [type, serial, name, room, OW, OW_time, status, info, temp offset]}
        # rooms = {id:	[room_name, room_address, is_win_open, curr_temp]}
        # valves = {valve_adr: [valve_pos, valve_temp, valve_curr_temp]}
        rooms = {}
        current = {}
        for k, v in self.rooms.iteritems():
            rooms.update({str(v[0]): ["", v[2]]})
            current.update({str(v[0]): {}})

        for k, v in self.valves.iteritems():
            # update rooms string
            room_id = self.get_room_name(k)
            cv = self.count_valve(k)
            if not cv:
                till = time.localtime(self.ignored_valves[k])
            else:
                till = 0
            current[room_id].update({str(k): [str(self.devices[k][2]), str(v[0]),
                                              str(v[1]), str(v[2]), str(1 if cv else 0), str(till)]})

        return json.dumps(current)

    def json_valve_status(self):
        current = {}
        for k, v in self.rooms.iteritems():
            current.update({str(v[0]): {}})

        for k, v in self.valves.iteritems():
            room_id = str(self.get_full_name(k)[0])
            cv = self.count_valve(k)
            current[room_id].update(
                {str(k): [str(self.devices[k][2]), str(v[0]), str(v[1]), str(v[2]), str(1 if cv else 0)]})

        return json.dumps(current)

    def nice(self):
        tmp_str = self.plain()
        tmp_str.replace("\r\n", "<br/>")
        tmp_str.replace("\t", "&#9;")
        return "<html>\r\n<title>\r\nStatus</title>\r\n<body>\r\n<p><pre>" + tmp_str + "</pre></p>\r\n</body>\r\n</html>"

    def headers(self, rn_vn=False):
        """
        Returns headers for CSV file in desired format
        :param rn_vn: boolean, if true then room name - valve name is generated
        :return: headers/string
        """
        tmp = ""
        for k, v in self.valves.iteritems():
            if rn_vn:
                room_id = str(self.get_full_name(k)[0])
                name = self.rooms[room_id][0] + "-" + self.devices[k][2]
            else:
                name = self.devices[k][2]
            tmp += name + "," + name + ","

        return tmp[:-1]

    def rooms_status(self):
        """ returns json in format address: [data] """
        # rooms = {id : [room_name, room_address, is_win_open, curr_temp]}
        tmp = {}
        for k, v in self.rooms.iteritems():
            tmp.update({v[1]: [v[0], v[2], v[3]]})
        return json.dumps(tmp)

    def valve_status(self):
        """ returns json in format address: [data] """
        # valves = {valve_adr: [valve_pos, valve_temp, valve_curr_temp, valve_name]}
        tmp = {}
        for k, v in self.valves.iteritems():
            valve_name = self.device_name(k)
            tmp.update({k: [v[0], v[1], v[2], valve_name]})
        return json.dumps(tmp)
