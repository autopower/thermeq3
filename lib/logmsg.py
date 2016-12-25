import os
import logging
import logging.handlers
import inspect

log_messages = []
logs = ['I', 'D', 'E']
logger = None


def update(message, log='D'):
    """
    Update list with message and log level
    :param message: string
    :param log: char, log selector
    :return:
    """
    global log_messages, logs
    if log in logs:
        log_messages.append([log, message])
    else:
        log_messages.append(['E', message])
    flush()


def debug(*args):
    """
    Converts arguments to strings, concat them and update log
    :param args: argument list
    :return: nothing
    """
    ln = len(args)
    if ln > 0:
        tmp_str = "## " + str(inspect.stack()[1][3]) + " ## "
        for i in range(0, ln):
            tmp_str += str(args[i])
        update(tmp_str, 'D')


def flush():
    """
    Flush log messages
    :return: nothing
    """
    global log_messages, logger
    # if list is not empty
    if log_messages:
        for k in log_messages:
            if k[0] == 'E':
                logger.error(k[1])
            elif k[0] == 'D':
                logger.debug(k[1])
            elif k[0] == 'I':
                logger.info(k[1])
            elif k[0] == 'C':
                logger.critical(k[1])
            else:
                logger.error("Wrong level: " + str(k[0]) + " message: " + str(k[1]))
        log_messages = []


def start(log_filename):
    """
    Start writing to time rotated log file
    :param log_filename: string
    :return:
    """
    global logger
    logger = logging.getLogger("thermeq3")
    logger.setLevel(logging.DEBUG)

    try:
        fh = logging.handlers.TimedRotatingFileHandler(log_filename, when="W0", interval=4, backupCount=12)
    except Exception:
        raise
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.info("Started with PID=" + str(os.getpid()))


def level(selector):
    """
    Changes log level
    :param selector: char
    :return: nothing
    """
    global logger
    if selector == 'D':
        logger.setLevel(logging.DEBUG)
    elif selector == 'I':
        logger.setLevel(logging.INFO)


def stop():
    """
    Stops logging
    :return: nothing
    """
    global logger
    logger.close()
