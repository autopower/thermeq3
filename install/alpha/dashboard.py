#!/usr/bin/env python
import urllib2
import json
import datetime
import urllib
import sys
import os
import subprocess

# Dashboard 0.50
a = {}
base_dir = "/home/pi/thermeq3"
valid_dates = {}
file_name = ""
top_menu = [["Status", "status"],
            ["Daily detail", "detail"],
            ["Heating summary", "summary"],
            ["Maintenance", "maintenance"],
            ["About", "about"]]
parameter = ""
date_param = ""
base_ip = "http://localhost/"
shell_result = "NULL"
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
    try:
        shell_result = subprocess.check_output(_command, shell=True)
    except Exception:
        shell_result = "Error"
    shell_result = shell_result.replace('\n', "<br/>")


def run_shell(_selector):
    if _selector == "generate":
        run_command("support/dailysum")
    elif _selector == "consolidate":
        run_command("support/consolidate")
    elif _selector == "zip":
        run_command("ls -al")


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

    if valid_dates == {}:
        get_files(base_dir)
    print """\t<script type="text/javascript">
    $(function () {
        $('#datetimepicker').datetimepicker({
            format:'DD/MM/YYYY',"""
    print "\t\t\tdefaultDate: moment(),"
    print """            
            enabledDates: ["""
    for k in valid_dates.iteritems():
        _d, _m, _y = return_dmy(k[0])
        print "\t\t\t\t", "'" + _y + "/" + _m + "/" + _d + "',"
    print """\t\t\t]
            }).on('dp.change', function (e) {
        console.log(e.date.format());
        window.location.href += "&date=" + e.date.format();
        })
    });
    </script>"""
    '''
    print """<script>
    $('.calpicker .datetimepicker').on('dp.change', function (e) {
        console.log(e.date.format());
        window.location.href += "&date=" + e.date.format();
        location.reload();
    });
    </script>
    """
    '''


def script_daily_detail(_file_name=""):
    global base_dir
    _full_name = base_dir + "/csv/" + _file_name
    if _file_name == "" or not os.path.isfile(_full_name):
        print_error("Resource error!" + _full_name)
        return

    print """
<script>
google.charts.load('current', {packages: ['corechart', 'bar']});
google.charts.setOnLoadCallback(drawBasicSummary);

function drawBasicSummary()
{
    var summary_data = google.visualization.arrayToDataTable(["""
    # get header from csv and print
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
    print "Content-type: text/html\n"
    print """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>thermeq3</title>
</head>
<script type="text/javascript" src="//code.jquery.com/jquery-2.1.1.min.js"></script>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>

<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.5.0/css/all.css" integrity="sha384-B4dIYHKNBt8Bc12p+WXckhzcICo0wtJAoU8YZTY5qE0Id1GSseTk6S+L3BlXeVIU" crossorigin="anonymous">

<script src="//cdnjs.cloudflare.com/ajax/libs/moment.js/2.9.0/moment-with-locales.js"></script>
<link href="//cdn.rawgit.com/Eonasdan/bootstrap-datetimepicker/e8bddc60e73c1ec2475f827be36e1957af72e2ea/build/css/bootstrap-datetimepicker.css" rel="stylesheet">
<script src="//cdn.rawgit.com/Eonasdan/bootstrap-datetimepicker/e8bddc60e73c1ec2475f827be36e1957af72e2ea/src/js/bootstrap-datetimepicker.js"></script>

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

<script type="text/javascript">
function fill_in(ch) {
    ip = location.host.split(':')[0];
    document.write('<input type="button" class="btn btn-outline-');
    if (ch == 'H') {
        document.write('success" value="Heat"');
    } else {
        document.write('danger" value="Stop"');
    }
    document.write('onclick=\"location.href=&quot;http://' + ip + '/data/put/msg/' + ch + '&quot;;">');
}
</script>"""


def page_top_menu_old(_selected=0):
    global top_menu
    print """<body>
    <nav class="navbar navbar-default">
      <div class="container-fluid">
        <div class="navbar-header">
          <a class="navbar-brand" href="#">thermeq3</a>
        </div>
        <ul class="nav navbar-nav">"""
    for _i in range(0, len(top_menu)):
        _tmp = "\t\t\t<li"
        if _i == _selected:
            _tmp += " class=\"active\""
        _tmp += "><a href=\"?cmd=" + top_menu[_i][1] + "\">" + top_menu[_i][0] + "</a></li>"
        print _tmp
    print """        </ul>
      </div>
    </nav>
<div class="container-fluid">"""


def page_top_menu(_selected=0):
    global top_menu
    print """<body>
<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <a class="navbar-brand" href="#">thermeq3</a>
        <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
    <ul class="navbar-nav mr-auto">

    <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">"""
    for _i in range(0, len(top_menu)):
        _tmp = "\t\t\t<li class=\"nav-item\""
        if _i == _selected:
            _tmp += " active"
        _tmp += "\"><a class=\"nav-link\" href=\"?cmd=" + top_menu[_i][1] + "\">" + top_menu[_i][0] + "</a></li>"
        print _tmp
    print """       </ul>
    </div>
</nav>
"""


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

        try:
            ydata = json.loads(urllib2.urlopen(yql_url).read())
        except Exception:
            pass
        else:
            if ydata is not None:
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
    print """
    <div class="row">
        <div class="col-md-12">
        <table class="table">
            <tbody>"""
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Actual date</td>\n\t\t\t\t\t<td>", datetime.datetime.now().strftime(
        "%d-%m-%Y %H:%M"), "</td>"
    print "\t\t\t\t\t<td>Bridge date</td>\n\t\t\t\t\t<td>", \
        datetime.datetime.fromtimestamp(float(a["touch"])), \
        "</td>\n\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Status</td>\n\t\t\t\t\t<td>", a["status"], \
        """<script>fill_in('H')</script>&nbsp;<script>fill_in('S')</script></td>"""
    print "\t\t\t\t\t<td>Autoupdate</td>\n\t\t\t\t\t<td>", a["autoupdate"], "</td>"
    print "\t\t\t\t</tr>"
    print "\t\t\t\t<tr>\n\t\t\t\t\t<td>Preference</td>\n\t\t\t\t\t<td>", a["preference"], "</td>"
    if a["preference"] == "per":
        str2 = a["valve_switch"]
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


def print_glyph_mask(_mask, _circle, _color=False, _alt_glyph=[]):
    if _mask == 0:
        _ret_str = get_glyph(True, _circle, _color, _alt_glyph)
    else:
        _ret_str = get_glyph(False, _circle, _color, _alt_glyph)
    print "\t\t\t\t\t\t" + get_td(_ret_str)


def get_td(_text):
    return "<td style=\"text-align: center;\">" + str(_text) + "</td>"


def get_glyph(_on, _circle=True, _color=False, _alt_glyph=[]):
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
    print ""
    b = a["system_status"]
    r = json.loads(b.replace("'", "\""), "UTF-8")
    owl = json.loads(a["open_window_list"].replace("'", "\""), "UTF-8")
    print """	<div class="row">
        <div class="col-md-12">
            <table class="table">
                <thead>
                    <tr>
                        <th>Room name</th>
                        <th>Valve name</th>
                        <th style="text-align: center;font-size:small;">Eval</th>
                        <th style="text-align: center;"><span style="font-size: 1.5em;"><i class="fas fa-percent"></i></span></th>
                        <th style="text-align: center;">Set&nbsp;<span style="font-size: 1.5em;"><i class="fas fa-thermometer-full"></span></i></th>
                        <th style="text-align: center;"><span style="font-size: 1.5em;"><i class="fas fa-thermometer"></i></span></th>
                        <th style="text-align: center;font-size:small;"><span style="font-size: 1.5em;"><i class="fab fa-windows"></i></span></th>
                        <th style="text-align: center;font-size:small;"><span style="font-size: 1.5em;"><i class="fas fa-th-large"></i></span></th>
                        <th style="text-align: center;font-size:small;"><span style="font-size: 1.5em;"><i class="far fa-keyboard"></i></span></th>
                        <th style="text-align: center;font-size:small;"><span style="font-size: 1.5em;"><i class="fas fa-link"></i></span></th>
                        <th style="text-align: center;font-size:small;"><span style="font-size: 1.5em;"><i class="fas fa-battery-full"></i></span></th>
                    </tr>
                </thead>
                <tbody>"""

    last_room = ""
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
            if y[4] == 0:
                ret_str += """<a href="#" data-toggle="tooltip" title="Ignored until """ + \
                    str(y[5]) + \
                    """"><span style="font-size: 1.5em; color: Red;"><i class="fas fa-info-circle"></i></span></a>"""
            print "\t\t\t\t\t\t<td>", ret_str, "</td>"

            # Valve
            print "\t\t\t\t\t\t<td><a href=\"#\" data-toggle=\"tooltip\" title=\"Address: " + str(x) + \
                  "\">" + str(y[0]) + "</a></td>"

            # Evaluated?
            print_glyph_mask(y[4] == "0", True, True)

            # Position
            if valve_is_off:
                ret_str = "Off"
            else:
                ret_str = y[1]
            print "\t\t\t\t\t\t<td style=\"text-align: center;\">", ret_str, "</td>"

            # Temperature set
            if valve_is_off:
                ret_str = "Off"
            else:
                ret_str = y[2]
                if float(y[2]) == 12.0:
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
        <div class="col-md-12">        
            <div class="form-group">
                <div class='input-group date' id='datetimepicker'>
                    <input type='text' class="form-control" id="calpicker" />
                    <span class="input-group-addon">
                        <span class="glyphicon glyphicon-calendar"></span>
                    </span>
                </div>
            </div>
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
    try:
        result = urllib2.urlopen(request)
        ret_value = result.read()
    except Exception:
        ret_value = "{}"
    return ret_value


if __name__ == '__main__':
    this_module = sys.modules[__name__]
    selector = 0

    if len(sys.argv) > 1:
        tmp_arg = sys.argv[1].split('&')
        for i in range(0, len(tmp_arg)):
            _tmp_str = tmp_arg[i].split('=')
            if _tmp_str[0] == "cmd":
                for j in range(0, len(top_menu)):
                    if top_menu[j][1] == _tmp_str[1]:
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
    try:
        tmp = a["weather_reference"].upper()
    except Exception:
        tmp = ""

    location = "823123"
    if not tmp == "LOCAL":
        data = read_page_url("location.json")
        d = json.loads(data)
        try:
            location = d["yahoo_location"]
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
    page_weather(location)
    page_t3_status()

    # noinspection PyUnboundLocalVariable
    to_call()

    page_footer()
    page_end()
