#!/usr/bin/env python
import urllib2
import json
import base64
import datetime
import time

a = {}


def page_start():
    print "Content-type: text/html\n"
    print """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>thermeq3</title>

<link href="../css/bootstrap.min.css" rel="stylesheet">
<link href="../css/style.css" rel="stylesheet">

</head>"""


def page_body_menu():
    print """<body>
    <div class="container-fluid">
    <div class="row">
        <div class="col-md-12">
            <nav class="navbar navbar-default" role="navigation">
                <div class="navbar-header">
                    <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
                    <span class="sr-only">Toggle navigation</span><span class="icon-bar"></span><span class="icon-bar"></span><span class="icon-bar"></span>
                    </button> <a class="navbar-brand" href="#">thermeq3 status</a>
                </div>
            </nav>
        </div>
    </div>"""


def page_body_status():
    global a
    print """
    <div class="row">
        <div class="col-md-12">
        <table class="table">
            <tbody>"""
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Actual date</td>\n\t\t\t\t\t<td>", datetime.datetime.now().strftime(
        "%d-%m-%Y %H:%M"), "</td>\n"
    print "\t\t\t\t\t<td>Bridge date</td>\n\t\t\t\t\t<td>", \
        datetime.datetime.fromtimestamp(float(a["touch"])), \
        "</td>\n\t\t\t\t</tr>"
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Status</td>\n\t\t\t\t\t<td>", a["status"], "</td>"
    print "\t\t\t\t\t<td>Autoupdate</td>\n\t\t\t\t\t<td>", a["autoupdate"], "</td>"
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Preference</td>\n\t\t\t\t\t<td>", a["preference"], "</td>"
    if a["preference"] == "per":
        str2 = a["valve_pos"]
    else:
        str2 = a["total_switch"]
    print "\t\t\t\t\t<td>Turning on</td>\n\t\t\t\t\t<td>", str2, "%</td>"
    print "\t\t\t\t</tr>"
    if a["preference"] == "per":
        print "\t\t\t\t<tr>\n\t\t\t\t\t<td># Valves</td>\n\t\t\t\t\t<td>", a["valves"], "</td>"
    print "\t\t\t\t\t<td>svpnmw</td>\n\t\t\t\t\t<td>", a["svpnmw"], "%</td>"
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Interval</td>\n\t\t\t\t\t<td>", a["interval"], "sec", "</td>"
    print "\t\t\t\t\t<td>Profile</td>\n\t\t\t\t\t<td>", a["profile"], "</td>\n\t\t\t\t</tr>"

    print """\t\t\t</tbody>
        </table>
        </div>
    </div>"""


def page_body_rooms():
    global a
    b = a["system_status"]
    r = json.loads(b.replace("'", "\""))
    owl = json.loads(a["open_window_list"].replace("'", "\""))
    print """	<div class="row">
        <div class="col-md-12">
            <table class="table">
                <thead>
                    <tr>
                        <th>Room</th>
                        <th>Valve name<br/>[Address]</th>
                        <th style="text-align: center;font-size:small;">Eval</th>
                        <th style="text-align: center;">%</th>
                        <th style="text-align: center;">Set<br/>Temp</th>
                        <th style="text-align: center;">Actual<br/>Temp</th>
                        <th style="text-align: center;font-size:small;">Win<br/>dows</th>
                        <th style="text-align: center;font-size:small;">Mode</th>
                        <th style="text-align: center;font-size:small;">Panel</th>
                        <th style="text-align: center;font-size:small;">Link</th>
                        <th style="text-align: center;font-size:small;">Battery</th>
                    </tr>
                </thead>
                <tbody>"""

    last_room = ""
    for k, v in r.iteritems():
        for x, y in v.iteritems():
            print "\t\t\t\t\t<tr>"
            # Room
            if k == last_room:
                ret_str = "&nbsp;"
            else:
                ret_str = k
            last_room = k
            print "\t\t\t\t\t\t<td>", ret_str, "</td>"
            # Valve
            print "\t\t\t\t\t\t<td>", y[0], "<br/>[" + str(x) + "]</td>"
            # Evaluated?
            ret_str = """\t\t\t\t\t\t<td align="center">"""
            if y[4] == "0":
                ret_str += "<a href=\"#\" data-toggle=\"tooltip\" title=\"Ignored until " + \
                           str(y[5]) + "\"><span class =\"glyphicon\">&#xe014;</span></td>"
            else:
                ret_str += "<span class =\"glyphicon\">&#xe013;</span></td>"
            ret_str += "</td>"
            print ret_str
            # Position
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", y[1], "</td>"
            # Temperature set
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", y[2], "</td>"
            # Temperature actual
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", y[3], "</td>"
            # Windows
            ret_str = "&#xe013;"
            for i, j in owl.iteritems():
                if j[1] == k:
                    ret_str = "&#xe014;"
                else:
                    ret_str = "&#xe013;"
            print """\t\t\t\t\t\t<td align="center"><span class="glyphicon">""" + ret_str + "</span></td>"
            # Mode
            mode = int(y[6])
            mask = mode & 0b00000011
            if mask == 0:
                ret_str = "Auto"
            elif mask == 1:
                ret_str = "Manual"
            elif mask == 2:
                ret_str = "Vacation"
            elif mask == 3:
                ret_str = "Boost"
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            # Status
            mask = mode & 0b00100000
            if mask == 0:
                ret_str = "<span class=\"glyphicon glyphicon-minus\"></span>"
            else:
                ret_str = "<span class=\"glyphicon glyphicon-lock\"></span>"
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            mask = mode & 0b01000000
            if mask == 0:
                ret_str = "<span class =\"glyphicon\">&#xe013;</span>"
            else:
                ret_str = "<span class =\"glyphicon\">&#xe014;</span>"
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            mask = mode & 0b10000000
            if mask == 0:
                ret_str = "<span class =\"glyphicon\">&#xe013;</span>"
            else:
                ret_str = "<span class =\"glyphicon\">&#xe014;</span>"
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            print "\t\t\t\t\t</tr>"
    print """
                </tbody>
            </table>
        </div>
    </div>"""


def page_footer():
    print """   <div class="row">
        <div class="col-md-12">
            <table align="center">
                <tr><td align="center"><a href="https://github.com/autopower/thermeq3">thermeq3 github</a></td></tr>
                <tr><td align="center"><a href="https://www.facebook.com/autopow/">Fanpage</a></td></tr>
                <tr><td align="center"><a href="mailto:autopowerdevice@gmail.com">Email</a></td></tr>
            </table>
        </div>
    </div>
</div>"""


def page_end():
    print "</body>\n</html>"


url = "http://10.60.0.11/data/get"
base64string = base64.encodestring('%s:%s' % ("root", "arduino")).replace('\n', '')
request = urllib2.Request(url)
request.add_header("Authorization", "Basic %s" % base64string)
result = urllib2.urlopen(request)
data = result.read()

d = json.loads(data)
a = d["value"]

b = ["touch", "status", "autoupdate", "preference", "valve_pos", "total_switch", "valves", "svpnmw", "interval", "profile"]
for i in b:
    if i not in a:
        a.update({i: ""})

page_start()
page_body_menu()
page_body_status()
page_body_rooms()
page_footer()
page_end()
