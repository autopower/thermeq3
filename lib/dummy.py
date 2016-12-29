import thermeq3
import datetime


def add_dummy(status):
    """
    :param status: is window open?
    :return: nothing
    """
    # valves = {valve_adr: [valve_pos, valve_temp, valve_curtemp, valve_name]}
    # rooms = {id : [room_name, room_address, is_win_open, curr_temp, average valve position]}
    # devices = {addr: [type, serial, name, room, OW, OW_time, status, info, temp offset]}
    thermeq3.t3.eq3.rooms.update({"99": ["Dummy room", "DeadBeefValve", False, 22.0, 22]})
    thermeq3.t3.eq3.devices.update({"DeadBeefWindow": [4, "IHADBW", "Dummy window", 99, 0,
                                                datetime.datetime(2016, 01, 01, 12, 00, 00), 18, 16, 7]})
    thermeq3.t3.eq3.devices.update({"DeadBeefValve": [1, "IHADBV", "Dummy valve", 99, 0,
                                               datetime.datetime(2016, 01, 01, 12, 00, 00), 18, 56, 7]})
    thermeq3.t3.eq3.valves.update({"DeadBeefValve": [20, 22.0, 22.0, "Dummy valve"]})
    # TBI open/closed window
    if status:
        thermeq3.t3.eq3.devices["DeadBeefWindow"][4] = 2
        thermeq3.t3.eq3.devices["DeadBeefWindow"][5] = \
            datetime.datetime.now() - \
            datetime.timedelta(seconds=((thermeq3.t3.eq3.ignore_time + 10) * 60))
        thermeq3.t3.eq3.rooms["99"][2] = True
    else:
        thermeq3.t3.eq3.devices["DeadBeefWindow"][4] = 0
        thermeq3.t3.eq3.rooms["99"][2] = False


def remove_dummy():
    del thermeq3.t3.eq3.rooms["99"]
    del thermeq3.t3.eq3.valves["DeadBeefValve"]
    del thermeq3.t3.eq3.devices["DeadBeefWindow"]
    del thermeq3.t3.eq3.devices["DeadBeefValve"]
