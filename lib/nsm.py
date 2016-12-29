#!/usr/bin/env python
import thermeq3
import httplib


def stop_httpd(port):
    """
    Send QUIT request to http server running on localhost:<port>
    :param port:
    :return:
    """
    conn = httplib.HTTPConnection("localhost:%d" % port)
    conn.request("QUIT", "/")
    conn.getresponse()

if __name__ == '__main__':
    thermeq3.start()
    thermeq3.loop()
