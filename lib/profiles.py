import logmsg
import datetime
import time
import bridge


class Profile(object):
    def __init__(self):
        """
        Init variables
        :rtype: object
        """
        self.day = []
        self.temp = []
        self.selected_mode = 0
        self.act_mode_idx = 0
        self.sit = {}

    def start(self, dt, tt):
        self.day = dt
        self.temp = tt


table = Profile()


def check_day_table():
    global table
    if len(table.day) > 1:
        for i in range(len(table.day) - 1):
            if time.strptime(table.day[i + 1][0], "%H:%M") <= time.strptime(table.day[i][0], "%H:%M"):
                logmsg.update("Day mode table is wrong! Using default table!", 'E')
                table.day = [["00:00", "23:59", 40, 185, "total", 120, 1]]


def time_in_range(start, end, x):
    today = datetime.date.today()
    start = datetime.datetime.combine(today, start)
    end = datetime.datetime.combine(today, end)
    x = datetime.datetime.combine(today, x)
    if end <= start:
        end += datetime.timedelta(1)  # tomorrow!
    if x <= start:
        x += datetime.timedelta(1)  # tomorrow!
    return start <= x <= end


def is_time():
    global table
    this_now = datetime.datetime.now().time()
    ret_value = -1
    for k in table.day:
        nf = datetime.datetime.strptime(k[0], "%H:%M").time()
        nt = datetime.datetime.strptime(k[1], "%H:%M").time()
        if time_in_range(nf, nt, this_now):
            ret_value = table.day.index(k)
    # logmsg.update("IsTime=" + str(ret_value))
    return ret_value


def time_mode():
    global table
    # day = [0-from_str, 1-to_str, 2-total or per, 3-mode ("total"/"per"), 4-check interval, 5-valves]
    md = is_time()
    # logmsg.update("Actual index=" + str(table.act_mode_idx), 'D')
    if md != -1:
        if md != table.act_mode_idx:
            kv = table.day[md]
            table.act_mode_idx = md
            logmsg.update("Switching day mode to " + str(md) + " = " + str(kv), 'I')
            return kv


def temp_mode():
    global table
    c_temp = int(table.sit["current_temp"])
    for k in table.temp:
        kv = table.temp[k]
        if kv[1] > c_temp >= kv[0]:
            table.act_mode_idx = k
            logmsg.update("Switching temp mode to " + str(kv[0]) + " ~ " + str(kv[1]), 'I')
            return kv


def do(sel_mode, act_idx, sit):
    """
    Performs day or temp mode selection
    :param sel_mode: char, selected mode
    :param act_idx:  integer, actual index
    :param sit: dictionary, weather situation
    :return: list
    """
    # update variables from main code
    global table
    table.selected_mode = sel_mode
    table.act_mode_idx = act_idx
    table.sit = sit
    tmp_prof = bridge.try_read("profile", "time", False).upper()
    kv = []
    if tmp_prof != table.selected_mode:
        table.selected_mode = tmp_prof
        table.act_mode_idx = -1
    if tmp_prof == "TIME":
        check_day_table()
        kv = time_mode()
    elif tmp_prof == "TEMP":
        kv = temp_mode()
    return [table.selected_mode, table.act_mode_idx, kv]


def init(dt, tt):
    """
    Init day and temp table
    :param dt: list, daytable
    :param tt: list, daytable
    :return: nothing
    """
    global table
    table.start(dt, tt)
