import struct
import socket
import urllib2
import os


def is_private(lookup_ip):
    """
    Returns True if IP address is private, False if not
    :param lookup_ip: ip address
    :return:  True
    """
    if os.name == "nt":
        f = struct.unpack('!I', socket.inet_aton(lookup_ip))[0]
    else:
        f = struct.unpack('!I', socket.inet_pton(socket.AF_INET, lookup_ip))[0]
    private = (
        [2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0   http://tools.ietf.org/html/rfc3330
        [3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0 http://tools.ietf.org/html/rfc1918
        [2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0 http://tools.ietf.org/html/rfc1918
        [167772160, 4278190080],  # 10.0.0.0,    255.0.0.0   http://tools.ietf.org/html/rfc1918
    )
    for net in private:
        if f & net[1] == net[0]:
            return True
    return False


def get():
    """
    Gets public IP, using service at ip.42.pl/raw address
    :return: ip address, if unsuccessful 0xFF
    """
    try:
        tmp_ip = str(urllib2.urlopen('http://ip.42.pl/raw').read())
    except Exception:
        try:
            tmp_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            tmp_ip = 0xFF
    return tmp_ip
