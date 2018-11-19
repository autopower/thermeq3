import logmsg
import os
import errno


sw = None


class SecWeb(object):
    def __init__(self):
        self.location = {}


#
# Global module functions
#
def init(location):
    """
    Setup variables
    :param location: where is secondary web directory
    :return: nothing
    """
    global sw
    sw = SecWeb()
    sw.location = {
        "status": str(location + "www/status.json"),
        "owl": str(location + "www/owl.json"),
        "nice": str(location + "www/nice.html"),
        "bridge": str(location + "www/bridge.json"),
        "loc": str(location + "www/location.json")}
    # check if exists directory for secondary web, if needed, create
    try:
        os.makedirs(location + "www")
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def write(cw, message):
    """
    Save message to file which is in secondary web directory
    :param message: message or string to write to file
    :param cw: string, selector what to save
    """
    global sw
    if cw in sw.location:
        fn = sw.location[str(cw)]
        try:
            swf = open(fn, "w")
        except IOError as e:
            logmsg.update("Error opening file " + fn + "! I/O error({0}): {1}".format(e.errno, e.strerror))
        except EnvironmentError:
            logmsg.update("Environment error while opening " + fn + "!", 'E')
        else:
            try:
                swf.write(str(message))
            except EnvironmentError:
                logmsg.update("Environment error while writing " + fn + "!", 'E')
            swf.close()
    else:
        logmsg.update("Wrong target [" + str(cw) + "] for saving file!", 'E')


def nice(message):
    message.replace("\n", "<br/>")
    message.replace("\t", "&#9;")
    write("nice", "<html>\n<title>\nStatus</title>\n<body>\n<p><pre>" + message + "</pre></p>\n</body>\n</html>")


def save_location(location):
    global sw
    try:
        f = open(sw.location["loc"], "w")
    except IOError:
        logmsg.update("IOError during opening location file for writing!", 'E')
    f.write(str({"location":str(location)}))
    f.close()
