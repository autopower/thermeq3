import os
import time
import logmsg


class CsvObject(object):
    def __init__(self):
        self.file = ""
        self.handle = None
        self.state = False
        self.place = ""
        self.dev_name = ""
        self._buffer = ""

    def __repr__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def is_init(self):
        return self.file == "" and self.place == "" and self.dev_name == ""

    def open(self):
        if self.is_init():
            raise NameError("Wrong init!")
        if os.path.exists(self.file):
            os.rename(self.file, self.place + self.dev_name + "_" + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".csv")
        try:
            self.handle = open(self.file, "a")
        except Exception:
            logmsg.update("Can't open CSV file: " + str(self.file))
            raise
        else:
            self.state = True

    def close(self):
        try:
            self.handle.flush()
        except:
            pass

        try:
            os.fsync(self.handle.fileno())
        except:
            pass

        try:
            self.handle.close()
        except Exception:
            logmsg.update("Can't close CSV file!")
        else:
            self.state = False

    def add(self, text):
        self._buffer += text + ","

    def write(self):
        if self._buffer[-1:] == ',':
            self._buffer = self._buffer[:-1]
        self.handle.write(self._buffer + "\n")
        self.handle.flush()
        self._buffer = ""

csv = CsvObject()


def is_init():
    """
    Is CSV initalized
    :return: boolean
    """
    global csv
    return csv.state


def init(place, dev_name):
    """
    Init CSV variables and open CSV file
    :param place:
    :param dev_name:
    :return: boolean
    """
    global csv
    if not place == "":
        if place[-1:] != '/':
            place += '/'
        place += "csv/"
        csv.place = place
    else:
        return False
    if not dev_name == "":
        csv.dev_name = dev_name
    else:
        return False
    csv.file = place + dev_name + ".csv"
    csv.state = True
    csv.open()


def close():
    global csv
    """
    Close CSV file
    :return: nothing
    """
    csv.close()


def write(*args):
    """
    Write arguments to CSV file
    :param args: arguments
    :return: nothing
    """
    global csv
    if not is_init:
        csv.open()
    ln = len(args)
    if ln > 0:
        for i in range(0, ln):
            if args[i] == "\n":
                csv.write()
            else:
                csv.add(str(args[i]))
