#!/usr/bin/env python
import urllib2
import json
import datetime
import urllib
import sys
import os
import subprocess
import uuid
import hmac
import hashlib
import time
from base64 import b64encode

# Dashboard version
dash_version = "0.56"
# Please edit these two lines
base_dir = "/home/pi/thermeq3"
base_ip = "http://localhost/"
#
a = {}
valid_dates = {}
file_name = ""
top_menu = [["Status", "status"],
            ["Daily detail", "detail"],
            ["Heating summary", "summary"],
            ["Maintenance", "maintenance"],
            ["Override", ["Manual start", "Manual stop"]],
            ["About", "about"]]
parameter = ""
date_param = ""
shell_result = "NULL"
platform = "rpi"
preference = []
'''
-------------------------------------------------
support
-------------------------------------------------
'''


def ddn():
    return datetime.datetime.now().strftime("%Y%m%d")


def return_dmy(date_str, _format=0, _separator=""):
    if not _separator == "":
        date_str = date_str.replace(_separator, '')
    if _format == 0:
        return date_str[6:8], date_str[4:6], date_str[0:4]
    elif _format == 1:
        return date_str[0:2], date_str[2:4], date_str[4:8]


def return_hms(time_str, _separator=""):
    if not _separator == "":
        time_str = time_str.replace(_separator, '')
    return time_str[0:2], time_str[2:4], time_str[4:6]


def get_correct_date(_date):
    return _date.replace('-', '')[0:8]


def get_files(_base_dir):
    global valid_dates
    global date_param
    global parameter

    # noinspection PyBroadException
    try:
        for f in os.listdir(_base_dir + "/csv"):
            if os.path.isfile(_base_dir + "/csv/" + f) and f.endswith(".csv"):
                _tmp = f[:-4].split("_")
                if len(_tmp) > 1:
                    _tmp = _tmp[1].split("-")
                    tmp_key = _tmp[0]
                    if tmp_key in valid_dates:
                        tmp_list = valid_dates[tmp_key]
                        tmp_list.append(f)
                        tmp_val = tmp_list
                    else:
                        tmp_val = [f]
                    valid_dates.update({_tmp[0]: tmp_val})
                    if date_param == _tmp[0]:
                        parameter = tmp_val[0]
    except Exception:
        valid_dates = {ddn(): "no_valid_file.csv"}


def print_error(_err_str):
    print "<p>", _err_str, "</p>"


def run_command(_command):
    global shell_result

    # noinspection PyBroadException
    try:
        shell_result = subprocess.check_output(_command, shell=True)
    except Exception:
        shell_result = "Error"
    shell_result = shell_result.replace('\n', "<br/>")


def run_shell(_selector):
    if _selector == "generate":
        run_command(base_dir + "/support/dailysum")
    elif _selector == "consolidate":
        run_command(base_dir + "/support/consolidate")
    elif _selector == "zip":
        run_command(base_dir + "/support/ziplog")


def get_platform_url():
    global base_ip

    if platform == "yun":
        _ret_str = base_ip.split(":")[0]
    else:
        _ret_str = base_ip
    if _ret_str[-1:] == "/":
        _ret_str = _ret_str[:-1]
    return _ret_str


def get_switch_link(onoff):
    global platform
    _tmp = ""
    if platform == "yun":
        _tmp = get_platform_url() + "/data/put/msg/" + ("H" if onoff else "S")
    else:
        _tmp = get_platform_url() + "/cgi-bin/test.sh?cmd=switch&resource=" + ("H" if onoff else "S")
    return _tmp


def embed_logo():
    return """data:image/png;base64,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"""


'''
-------------------------------------------------
scripts
-------------------------------------------------
'''


def script_replace_url():
    print """<script type="text/javascript">
var clean_uri = location.protocol + "//" + location.host + location.pathname + "?cmd=detail";
window.history.replaceState({}, document.title, clean_uri);
</script>"""


def script_print_calendar():
    global valid_dates
    global date_param

    if valid_dates == {}:
        get_files(base_dir)
    print """\t<script type="text/javascript">
    $(function () {
        $('#datetimepicker1').datetimepicker({
            format:'DD/MM/YYYY',"""
    if date_param == "":
        print "\t\t\tdefaultDate: moment(),"
    else:
        _d, _m, _y = return_dmy(date_param)
        print "\t\t\tdefaultDate:" + "'" + _y + "/" + _m + "/" + _d + "', "
    print """            enabledDates: ["""
    _tmp = "\t\t\t\t"
    for k in valid_dates.iteritems():
        _d, _m, _y = return_dmy(k[0])
        # print "\t\t\t\t", "'" + _y + "/" + _m + "/" + _d + "',"
        _tmp += "'" + _y + "/" + _m + "/" + _d + "', "
    print _tmp[:-2]
    print """\t\t\t]
            });
        $("#datetimepicker1").on("change.datetimepicker", function (e) {
            window.location.href += "&date=" + e.date.format();            
        });
    });
    </script>"""


def script_daily_detail(_file_name=""):
    global base_dir

    _full_name = base_dir + "/csv/" + _file_name
    if _file_name == "" or not os.path.isfile(_full_name):
        print """
    <div class="row">
        <div class="col-md-12">
            <p>Please select date:</p>
         </div>
    </div>
        """
        return

    print """
<script>
google.charts.load('current', {packages: ['corechart', 'bar']});
google.charts.setOnLoadCallback(drawBasicSummary);

function drawBasicSummary()
{
    var summary_data = google.visualization.arrayToDataTable(["""
    # get header from csv and print
    # noinspection PyBroadException
    try:
        with open(_full_name) as f:
            content = f.read().splitlines()
    except Exception:
        print_error("Error reading resource!")
    else:
        tmp_str = "["
        for v in content[0].split(','):
            if not v == "":
                tmp_str += "'" + v + "',"
        print "\t\t\t\t", tmp_str[:-1] + "],"
        _max_col = len(content[0].split(',')) - 3
        del content[0]
        for v in content:
            _tmp = v[:-1].split(',')
            _d, _m, _y = return_dmy(_tmp[0], 1, '/')
            _h, _mm, _s = return_hms(_tmp[0].split(' ')[1], ':')
            tmp_str = "["
            tmp_str += "new Date(" + _y + "," + _m + "," + _d + "," + _h + "," + _mm + "," + _s + ")"
            tmp_str += "," + str(int(_tmp[1]) * 100) + "," + str(int(_tmp[2]) * 100) + ","
            for _i in range(3, len(_tmp)):
                tmp_str += _tmp[_i]
                if _i < len(_tmp) - 1:
                    tmp_str += ","
            tmp_str += "],"
            print "\t\t\t\t", tmp_str
        print "]);"

        print """var summary_options = {"""
        print "    title : '", _file_name, "',"
        print """    vAxes: {1: {title:'DegC'}, 0: {title: '%'}},
        hAxis: {title: 'Time'},
        enableInteractivity: true,
        height: 400,
        seriesType: 'line',
        series: {0: {type: 'bars'}, 1: {type: 'bars'},"""
        for _i in range(1, _max_col + 1):
            if _i % 2 == 0:
                tmp_str = str(_i + 3) + ": {type: \"line\", targetAxisIndex: 1, lineDashStyle: [4,4]}"
                if _i < _max_col:
                    tmp_str += ","
                print "\t\t\t", tmp_str
        print """      }
        };
        
        var chart = new google.visualization.ComboChart(document.getElementById('chart_summary_div'));
        chart.draw(summary_data, summary_options);
        }"""
        print """</script>"""


def script_daily_summary():
    tmp_data = read_page_url("dailysummary.csv")

    print """<script>
    google.charts.load('current', {packages: ['corechart', 'bar']});
    google.charts.setOnLoadCallback(drawBasic);

    function drawBasic() {
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Day');
        data.addColumn('number', 'Heat [sec]');"""
    print "\tdata.addRows(["
    for line in tmp_data.splitlines():
        tmp_line = line.split(",")
        tmp_date = tmp_line[0].split("/")
        tmp_time = tmp_line[1].split(":")
        tmp_str_date = "new Date(" + tmp_date[0] + ", " + str(int(tmp_date[1]) - 1) + ", " + tmp_date[2] + ")"
        tmp_str_time = "{v:" + str(int(tmp_time[0]) * 3600 + int(tmp_time[1]) * 60 + int(tmp_time[2])) + ", f: '" + \
                       tmp_line[1] + "'}"
        print "\t\t\t[" + tmp_str_date + ", " + tmp_str_time + '],'
    print "]);"

    print """
    var options = {
        title: 'Heating duration per day',
        hAxis: {
            title: 'Date',
            format: 'dd/MM/yyyy'
        },
        vAxis: {
            title: 'Time'
        }
    };

    var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
    chart.draw(data, options);

    var button = document.getElementById('change');
    button.onclick = function () {
          // If the format option matches, change it to the new option,
          // if not, reset it to the original format.
          options.hAxis.format === 'dd/MM/yyyy' ?
          options.hAxis.format = 'dd MMM yyyy' :
          options.hAxis.format = 'dd/MM/yyyy';
          chart.draw(data, options);
        }

        var date_formatter = new google.visualization.DateFormat({pattern: "dd/MMM/yyyy"}); 
        date_formatter.format(data, 0);
    }
</script>
"""


'''
-------------------------------------------------
main subs
-------------------------------------------------
'''


def page_start():
    global dash_version

    print "Content-type: text/html\n"
    print """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>thermeq3</title>
</head>
<script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.18.1/moment-with-locales.min.js"></script>

<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.5.0/css/all.css" integrity="sha384-B4dIYHKNBt8Bc12p+WXckhzcICo0wtJAoU8YZTY5qE0Id1GSseTk6S+L3BlXeVIU" crossorigin="anonymous">

<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/5.0.0-alpha14/js/tempusdominus-bootstrap-4.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tempusdominus-bootstrap-4/5.0.0-alpha14/css/tempusdominus-bootstrap-4.min.css" />
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
"""
    print "<meta version=\"" + dash_version + "\">"


def page_top_menu(_selected=0):
    global top_menu
    print """<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light">"""
    print """\t\t<a class="navbar-brand" href="#"><img src=\"""" + embed_logo() + \
        """\" class="d-inline-block align-middle" width="40" height="40">&nbsp;thermeq3</a>"""
    print """        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
    <ul class="navbar-nav mr-auto">

    <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">"""
    for _i in range(0, len(top_menu)):
        if type(top_menu[_i][1]) is list:
            _tmp = """\t\t\t<li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdownMenuLink" data-toggle="dropdown" """ \
                   """aria-haspopup="true" aria-expanded="false">"""
            _tmp += str(top_menu[_i][0])
            _tmp += """
        </a>
        <div class="dropdown-menu" aria-labelledby="navbarDropdownMenuLink">"""
            for _j in top_menu[_i][1]:
                _tmp += "<a class=\"dropdown-item\" href=\"http://"
                if "start" in _j:
                    _tmp += get_switch_link(True) + "\"><button type=\"button\" class=\"btn btn-success\">" + _j + \
                        "</button></a>"
                elif "stop" in _j:
                    _tmp += get_switch_link(False) + "\"><button type=\"button\" class=\"btn btn-danger\">" + _j + \
                        "</button></a>"
                else:
                    _tmp += "#" + "\">" + _j + "</a>"
            _tmp += """        </div>
      </li>"""
        else:
            _tmp = "\t\t\t<li class=\"nav-item\""
            if _i == _selected:
                _tmp += " active"
            _tmp += "\"><a class=\"nav-link\" href=\"?cmd=" + top_menu[_i][1] + "\">" + top_menu[_i][0] + "</a></li>"
        print _tmp
    print """       </ul>
    </div>
</nav>
"""


# noinspection PyBroadException
def page_new_yahoo_weather(woe_id, yahoo_data):
    print """<div class="container-fluid">"""
    city, temp, humidity, text = "Error city", 0.0, 0.0, "init"
    if woe_id is None:
        city, temp, humidity, text = "WOEID None", -1.0, -1.0, "Error"
    else:
        # basic info
        url = 'https://weather-ydn-yql.media.yahoo.com/forecastrss'
        method = 'GET'
        try:
            data = json.loads(yahoo_data)
        except Exception:
            city, temp, humidity = "Error city", None, None
        else:
            app_id = str(data["app_id"])
            consumer_key = str(data["consumer_key"])
            consumer_secret = str(data["consumer_secret"])
            concat = '&'
            query = {'woeid': str(woe_id), 'format': 'json', 'u': 'c'}
            oauth = {
                'oauth_consumer_key': consumer_key,
                'oauth_nonce': uuid.uuid4().hex,
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(time.time())),
                'oauth_version': '1.0'
            }

            # Prepare signature string (merge all params and SORT them)
            merged_params = query.copy()
            merged_params.update(oauth)
            sorted_params = [k + '=' + urllib.quote(merged_params[k], safe='') for k in sorted(merged_params.keys())]
            signature_base_str = method + concat + urllib.quote(url, safe='') + concat + urllib.quote(
                concat.join(sorted_params), safe='')

            # Generate signature
            composite_key = urllib.quote(consumer_secret, safe='') + concat
            oauth_signature = b64encode(hmac.new(composite_key, signature_base_str, hashlib.sha1).digest())

            # Prepare Authorization header
            oauth['oauth_signature'] = oauth_signature
            auth_header = 'OAuth ' + ', '.join(['{}="{}"'.format(k, v) for k, v in oauth.iteritems()])

            # Send request
            url = url + '?' + urllib.urlencode(query)
            request = urllib2.Request(url)
            request.add_header('Authorization', auth_header)
            request.add_header('Yahoo-App-Id', app_id)
            try:
                data = urllib2.urlopen(request).read()
            except Exception, error:
                pass
            else:
                if data is not None:
                    data = json.loads(data)
                    try:
                        city = data["location"]["city"]
                        temp = float(data["current_observation"]["condition"]["temperature"])
                        humidity = int(data["current_observation"]["atmosphere"]["humidity"])
                        text = data["current_observation"]["condition"]["text"]
                    except Exception:
                        city, temp, humidity, text = "Error city", 0.0, 0.0, "Exception"

    print """\t<div class="row" style="margin-top: 8pt; margin-bottom: 8pt;">
        <div class="col-md-12">"""
    print "\t\t<h5>Weather in <b>" + str(city) + "</b>, <b>" + str(text) + "</b>, temperature: <b>" + str(temp) + \
          "</b>, humidity: <b>" + str(humidity) + "</b></h5>"
    print """\t\t</div>
    </div>"""


def page_weather(woeid):
    """
    Returns weather from yahoo weather from given WOEID
    :param woeid: integer, yahoo weather ID
    """
    print """<div class="container-fluid">"""
    city, temp, humidity, text = "Error city", 0.0, 0.0, "init"
    if woeid is None:
        city, temp, humidity, text = "WOEID None", -1.0, -1.0, "Error"
    else:
        # please change u='c' to u='f' for fahrenheit below
        base_url = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
        yql_url = base_url + urllib.urlencode({'q': yql_query}) + "&format=json"
        # noinspection PyBroadException
        try:
            ydata = json.loads(urllib2.urlopen(yql_url).read())
        except Exception:
            pass
        else:
            if ydata is not None:
                # noinspection PyBroadException
                try:
                    city = ydata["query"]["results"]["channel"]["location"]["city"]
                    temp = int(ydata["query"]["results"]["channel"]["item"]["condition"]["temp"])
                    humidity = int(ydata["query"]["results"]["channel"]["atmosphere"]["humidity"])
                    text = ydata["query"]["results"]["channel"]["item"]["condition"]["text"]
                except Exception:
                    city, temp, humidity, text = "Error city", 0.0, 0.0, "Exception"
    print """\t<div class="row" style="margin-top: 8pt; margin-bottom: 8pt;">
        <div class="col-md-12">"""
    print "\t\t<h5>Weather in <b>" + str(city) + "</b>, <b>" + str(text) + "</b>, temperature: <b>" + str(temp) + \
          "</b>, humidity: <b>" + str(humidity) + "</b></h5>"
    print """\t\t</div>
    </div>"""


def page_t3_status():
    global a
    global preference

    print """
    <div class="row">
        <div class="col-md-12">
        <table class="table">
            <tbody>"""
    _now = datetime.datetime.now()
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Actual date</td>\n\t\t\t\t\t<td>", _now.strftime(
        "%d. %b %Y %H:%M"), "</td>"
    _bridge_now = datetime.datetime.fromtimestamp(float(a["touch"]))
    _tmp = "\t\t\t\t\t<td>Bridge date</td>\n\t\t\t\t\t<td>" + _bridge_now.strftime("%d. %b %Y %H:%M")
    if _now - _bridge_now > datetime.timedelta(seconds=180):
        _tmp += "&nbsp; <span><a href=\"#\" data-toggle=\"tooltip\" " \
                "title=\"Big difference between bridge and actual time\" " \
                "class=\"fas fa-skull-crossbones\" style=\"color: red;\"></i></a></span>"
    print _tmp + "</td>\n\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Status</td>\n\t\t\t\t\t<td>", a["status"], """</td>"""
    print "\t\t\t\t\t<td>Autoupdate</td>\n\t\t\t\t\t<td>", a["autoupdate"], "</td>"
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Preference</td>\n\t\t\t\t\t<td>", a["preference"], "</td>"
    if a["preference"] == "per":
        str2 = a["valve_switch"]
        preference = ['p', int(str2)]
    else:
        str2 = a["total_switch"]
        preference = ['t', int(str2)]
    print "\t\t\t\t\t<td>Turning on</td>\n\t\t\t\t\t<td>", str2, "%</td>"
    print "\t\t\t\t</tr>"
    if a["preference"] == "per":
        print "\t\t\t\t<tr>\n\t\t\t\t\t<td># Valves</td>\n\t\t\t\t\t<td>", a["valves"], "</td>"
        preference.append(int(a["valves"]))
    else:
        preference.append(-1)
    print "\t\t\t\t\t<td>svpnmw</td>\n\t\t\t\t\t<td>", a["svpnmw"], "%</td>"
    preference.append(int(a["svpnmw"]))
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Interval</td>\n\t\t\t\t\t<td>", a["interval"], "sec", "</td>"
    print "\t\t\t\t\t<td>Profile</td>\n\t\t\t\t\t<td>", a["profile"], "</td>\n\t\t\t\t</tr>"

    print """\t\t\t</tbody>
        </table>
        </div>
    </div>"""


def print_glyph_mask(_mask, _circle, _color=False, _alt_glyph=None):
    if _alt_glyph is None:
        _alt_glyph = []
    if _mask == 0:
        _ret_str = get_glyph(True, _circle, _color, _alt_glyph)
    else:
        _ret_str = get_glyph(False, _circle, _color, _alt_glyph)
    print "\t\t\t\t\t\t" + get_td(_ret_str)


def get_td(_text):
    return "<td style=\"text-align: center;\">" + str(_text) + "</td>"


def get_glyph(_on, _circle=True, _color=False, _alt_glyph=None):
    if _alt_glyph is None:
        _alt_glyph = []
    if _color:
        if _on:
            _col_str = " color: GreenYellow;"
        else:
            _col_str = " color: Red;"
    else:
        _col_str = ""

    if len(_alt_glyph) < 2:
        _alt_glyph = ["far fa-check-square", "fas fa-times"]

    if _on:
        if _circle:
            _glyph = "far fa-check-circle"
        else:
            _glyph = _alt_glyph[0]
    else:
        if _circle:
            _glyph = "far fa-times-circle"
        else:
            _glyph = _alt_glyph[1]

    return "<span style=\"font-size: 1.5em;" + _col_str + "\"><i class=\"" + _glyph + "\"></i></span>"


def page_status():
    global a
    global preference
    print ""

    b = a["system_status"]
    r = json.loads(b.replace("'", "\""), "UTF-8")
    owl = json.loads(a["open_window_list"].replace("'", "\""), "UTF-8")
    print """	<div class="row">
        <div class="col-md-12">
            <table class="table">
                <thead>
                    <tr style="text-align: center;">
                        <th style="text-align: left;">Room name</th>
                        <th style="text-align: left;">Valve name</th>
                        <th>Eval</th>
                        <th style="text-align: right;"><span><i class="fas fa-percent"></i></span></th>
                        <th>Set&nbsp;<span><i class="fas fa-thermometer-full"></span></i></th>
                        <th><span><i class="fas fa-thermometer"></i></span></th>
                        <th><span><i class="fab fa-windows"></i></span></th>
                        <th><span><i class="fas fa-th-large"></i></span></th>
                        <th><span><i class="far fa-keyboard"></i></span></th>
                        <th><span><i class="fas fa-link"></i></span></th>
                        <th><span><i class="fas fa-battery-full"></i></span></th>
                    </tr>
                </thead>"""

    last_room = ""
    valve_count = 0
    valve_sum = 0
    for k, v in r.iteritems():
        for x, y in v.iteritems():
            if y[2] == "4.5" and int(y[6]) & 0b00000011 == 1:
                valve_is_off = True
            else:
                valve_is_off = False
            if valve_is_off:
                print "\t\t\t\t\t<tr style=\"background-color: #D0D0D0;\">"
            else:
                print "\t\t\t\t\t<tr>"
            # Room
            if k == last_room:
                ret_str = "&nbsp;"
            else:
                ret_str = k
            last_room = k
            print "\t\t\t\t\t\t<td>", ret_str, "</td>"

            # Valve
            ret_str = "<a href=\"#\" data-toggle=\"tooltip\" title=\"Address: " + str(x) + \
                "\">" + str(y[0]) + "</a>"
            if int(y[4]) == 0:
                ret_str += """&nbsp;<a href="#" data-toggle="tooltip" title="Ignored until """ + \
                    str(y[5]) + \
                    """"><span style="font-size: 1em;"><i class="fas fa-info-circle"></i></span></a>"""
            print "\t\t\t\t\t\t<td>", ret_str, "</td>"
            
            # Evaluated?
            print_glyph_mask(y[4] == "0", True, True)

            # Position
            if valve_is_off:
                ret_str = "Off"
            else:
                ret_str = y[1]
                if int(y[1]) > preference[3]:
                    ret_str = "<i class=\"fas fa-bookmark\"></i>&nbsp;" + ret_str
                elif preference[0] == 'p':
                    if int(y[1]) > preference[1]:
                        ret_str = "<i class=\"far fa-bookmark\"></i>&nbsp;" + ret_str
                        if not k == last_room:
                            valve_count += 1
                elif preference[0] == 't':
                    valve_sum += int(y[1])
            print "\t\t\t\t\t\t<td style=\"text-align: right;\">", ret_str, "</td>"

            # Temperature set
            if valve_is_off:
                ret_str = "Off"
            else:
                ret_str = y[2]
                if float(y[2]) == 12.0 and y[4] == "0":
                    ret_str += """<br/><a href="#" data-toggle="tooltip" title="Possible open window because """ \
                        """temperature 12.0 degC. Check windows">""" \
                        """<span style="color: Red;"><i class="fas fa-exclamation-triangle"></i>""" \
                        """</span></a>"""
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            # Temperature actual
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", y[3], "</td>"

            # Windows
            _tmp_rooms = []
            ret_str = "<span style=\"font-size: 1.5em; color: "
            for _i, _j in owl.iteritems():
                _tmp_rooms.append(_j[1])
            print_glyph_mask(k in _tmp_rooms, False, True)

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
            if valve_is_off:
                ret_str = "Off"
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            # Panel
            print_glyph_mask(mode & 0b00100000, False, False, ["fas fa-lock-open", "fas fa-lock"])
            # Link
            print_glyph_mask(mode & 0b01000000, True)
            # Battery
            print_glyph_mask(mode & 0b10000000, True)

            print "\t\t\t\t\t</tr>"
    if preference[0] == 't':
        if valve_sum > preference[1]:
            ret_str = "<i class=\"fas fa-bookmark\"></i>&nbsp;"
        else:
            ret_str = ""
        print """\t\t\t\t\t<tr>
                        <td colspan="2">&nbsp;</td><td style="text-align: right;"><b>Total:</b></td>""" \
              """<td style="text-align: right;"><b>""" + ret_str + str(valve_sum) + \
              """</b></td><td colspan="7"></td></tr>"""
    print """
                </tbody>
            </table>
        </div>
    </div>"""


def page_summary():
    script_daily_summary()
    print """
    <div class="row">
        <div class="col-md-12">        
            <button id="change">Click to change the format</button>
            <div id="chart_div"></div>
        </div>
    </div>
    """


def page_detail():
    global parameter
    script_print_calendar()
    script_daily_detail(parameter)

    print """
    <div class="row">
        <div class="col-md-3">        
            <div class="form-group">
                <div class="input-group date" id="datetimepicker1" data-target-input="nearest">
                    <input type="text" class="form-control datetimepicker-input" data-target="#datetimepicker1" />
                    <div class="input-group-append" data-target="#datetimepicker1" data-toggle="datetimepicker">
                        <div class="input-group-text"><i class="fa fa-calendar"></i></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-12">
            <div id="chart_summary_div"></div>            
        </div>
    </div>
    """


def page_about():
    pass


def page_maintenance():
    global shell_result
    print """
    <div class="row">
        <div class="col-md-3 text-center">        
            <p><a href="?cmd=generate" class="btn btn-primary" role="button">Generate daily summary</a></p>
            <p><a href="?cmd=consolidate" class="btn btn-primary" role="button">Consolidate CSV</a></p>
            <p><a href="?cmd=zip" class="btn btn-primary" role="button">Zip CSV</a></p>
        </div>
        <div class="col-md-9">        
            <h4>Output</h4>
            <blockquote class="blockquote">""" + shell_result + """</blockquote>    
        </div>
        
    </div>
    """


def page_footer():
    print """
    <div class="row">
        <div class="col-md-3" style="text-align: center">&nbsp;</div>
        <div class="col-md-2" style="text-align: center">
            <a href="https://github.com/autopower/thermeq3"><i class="fab fa-github"></i>&nbsp;thermeq3</a>
        </div>
        <div class="col-md-2" style="text-align: center">
            <a href="https://www.facebook.com/autopow/"><i class="fab fa-facebook-square"></i>&nbsp;autopower</a>
        </div>
        <div class="col-md-2" style="text-align: center">
            <a href="mailto:autopowerdevice@gmail.com"><span class="fas fa-envelope"></span>&nbsp;Email</a>
        </div>
        <div class="col-md-3" style="text-align: center">&nbsp;</div>
    </div>"""


def page_end():
    print "\t</div>\n</body>\n</html>"


def sys_argv():
    global parameter

    print """
    <div class="row">
        <div class="col-md-6">"""
    print sys.argv
    print "        </div>"
    print "</div>"


def read_page_url(url):
    global base_ip

    request = urllib2.Request(base_ip + str(url))
    # noinspection PyBroadException
    try:
        result = urllib2.urlopen(request)
        ret_value = result.read()
    except Exception:
        ret_value = "{}"
    return ret_value


def page_switch():
    pass


if __name__ == '__main__':
    this_module = sys.modules[__name__]
    selector = 0

    if len(sys.argv) > 1:
        tmp_arg = sys.argv[1].split('&')
        for i in range(0, len(tmp_arg)):
            _tmp_str = tmp_arg[i].split('=')
            if _tmp_str[0] == "cmd":
                for j in range(0, len(top_menu)):
                    if top_menu[j][1] == _tmp_str[1] or _tmp_str[1] == "switch":
                        to_call = getattr(this_module, "page_" + _tmp_str[1])
                        if callable(to_call):
                            pass
                        selector = j
            elif _tmp_str[0] == "resource":
                parameter = _tmp_str[1]
            elif _tmp_str[0] == "date":
                date_param = get_correct_date(_tmp_str[1])
            elif _tmp_str[0] == "generate":
                run_shell("generate")
                to_call = page_maintenance
            elif _tmp_str[0] == "consolidate":
                run_shell("consolidate")
                to_call = page_maintenance
            elif _tmp_str[0] == "zip":
                run_shell("zip")
                to_call = page_maintenance
    else:
        to_call = getattr(this_module, "page_status")

    data = read_page_url("bridge.json")
    a = json.loads(data)
    # noinspection PyBroadException
    try:
        tmp = a["weather_reference"].upper()
    except Exception:
        tmp = ""

    location = "823123"
    if not tmp == "LOCAL":
        data = read_page_url("location.json")
        d = json.loads(data)
        # noinspection PyBroadException
        try:
            location = d["yahoo_location"]
            yahoo_data = d["yahoo"]
        except Exception:
            pass

    cws = ["touch", "status", "autoupdate", "preference", "valve_switch", "total_switch", "valves",
           "svpnmw", "interval", "profile", "yahoo_location", "weather_reference"]
    for cw in cws:
        if cw not in a:
            a.update({cw: ""})

    page_start()
    page_top_menu(selector)
    if not date_param == "":
        script_replace_url()
    # sys_argv()
    page_new_yahoo_weather(location, yahoo_data)
    page_t3_status()

    # noinspection PyUnboundLocalVariable
    to_call()

    page_footer()
    page_end()
