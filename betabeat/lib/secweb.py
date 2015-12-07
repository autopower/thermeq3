import logmsg
import os
import errno


class SecWeb(object):
    def __init__(self):
        self.location = {}

    def start(self, location):
        """
        Setup variables
        :param location: where is secondary web directory
        :return: nothing
        """
        self.location = {
            "status": str(location + "www/status.xml"),
            "owl": str(location + "www/owl.xml"),
            "nice": str(location + "www/nice.html")}
        # check if exists directory for secondary web, if no, create
        try:
            os.makedirs(location + "www")
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    def write(self, cw, message):
        """
        saves txt to file which is in secondary web directory
        :param message: message/string to write to file
        :param cw: string, selector what to save
        """
        if cw in self.location:
            fn = self.location[str(cw)]
            try:
                swf = open(fn, "w")
            except Exception:
                logmsg.update("Error writing to file " + fn + "!", 'E')
            else:
                swf.write(str(message))
                swf.close()
        else:
            logmsg.update("Wrong target [" + str(cw) + "] for saving file!", 'E')
