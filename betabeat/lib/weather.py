import urllib
import urllib2
import logmsg
import traceback
from math import exp
import json


def weather_for_woeid(woeid):
    """
    Returns weather from yahoo weather from given WOEID
    :param woeid: integer, yahoo weather ID
    :return: dictonary, {"current_temp": temp, "city": city, "humidity": humidity}
    """
    # please change u='c' to u='f' for farenheit below
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
    yql_url = baseurl + urllib.urlencode({'q': yql_query}) + "&format=json"

    try:
        result = urllib2.urlopen(yql_url).read()
        data = json.loads(result)
    except Exception, error:
        logmsg.update("Yahoo communication error: " + str(error), 'E')
        logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
        city = "Error city"
        temp = 0
        humidity = 50
    else:
        city = data["query"]["results"]["channel"]["location"]["city"]
        temp = int(data["query"]["results"]["channel"]["item"]["condition"]["temp"])
        humidity = int(data["query"]["results"]["channel"]["atmosphere"]["humidity"])

        # and check if yahoo is correct, PLEASE USE OWN API KEY!!!
        url = "http://api.openweathermap.org/data/2.5/weather?q=" + str(city) + \
              "&appid=2de143494c0b295cca9337e1e96b00e0"
        try:
            result = json.load(urllib2.urlopen(url))
        except Exception, error:
            logmsg.update("OWM communication error: " + str(error), 'E')
            logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
        else:
            owm_temp = abs(round(result["main"]["temp"] / 100))
            yho_temp = abs(round(temp))
            if abs(yho_temp - owm_temp) > 1.5:
                logmsg.update("Difference between Yahoo and OWM temperatures. Yahoo=" + str(yho_temp) +
                              " OWM=" + str(owm_temp), 'I')
                # end check
        logmsg.update(
            "Current temperature in " + str(city) + " is " + str(temp) + ", humidity " + str(humidity) + "%", 'I')

    return {
        "current_temp": temp,
        "city": city,
        "humidity": humidity
    }


def _scale(val, src, dst):
    """ Scale the given value from the scale of src to the scale of dst
    :param val: float, value to scale
    :param src: list, scale interval from
    :param dst: list, scale interval to
    :return: float
    """
    return ((val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]


def interval_scale(temp, t, r, w, test):
    if test:
        if temp < t[0]:
            temp = t[0]
        elif temp > t[1]:
            temp = t[1]

    a = _scale(temp, t, r)
    b = int(_scale(exp(a), (exp(r[0]), exp(r[1])), w))

    return b
