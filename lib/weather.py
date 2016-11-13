import urllib
import urllib2
import logmsg
import traceback
from math import exp
import json


def weather_for_woeid(woeid, owm_api_key):
    """
    Returns weather from yahoo weather from given WOEID
    :param owm_api_key:
    :param woeid: integer, yahoo weather ID
    :return: dictionary, {"current_temp": temp, "city": city, "humidity": humidity}
    """
    city = "Error city"
    temp = None
    humidity = None
    # please change u='c' to u='f' for fahrenheit below
    base_url = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
    yql_url = base_url + urllib.urlencode({'q': yql_query}) + "&format=json"

    try:
        result = urllib2.urlopen(yql_url).read()
        data = json.loads(result)
    except Exception, error:
        logmsg.update("Yahoo communication error: " + str(error), 'E')
        logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
    else:
        if data is not None:
            try:
                city = data["query"]["results"]["channel"]["location"]["city"]
                temp = int(data["query"]["results"]["channel"]["item"]["condition"]["temp"])
                humidity = int(data["query"]["results"]["channel"]["atmosphere"]["humidity"])
            except Exception:
                pass
            else:
                # and check if yahoo is correct
                url = "http://api.openweathermap.org/data/2.5/weather?q=" + str(city) + "&appid=" + owm_api_key
                try:
                    result = json.load(urllib2.urlopen(url))
                except Exception, error:
                    logmsg.update("OWM communication error: " + str(error), 'E')
                    logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
                else:
                    if "main" in result:
                        owm_temp = round(result["main"]["temp"] / 100)
                        yho_temp = round(temp)
                        if abs(yho_temp - owm_temp) > 1.5:
                            logmsg.update("Difference between Yahoo and OWM temperatures. Yahoo=" + str(yho_temp) +
                                          " OWM=" + str(owm_temp), 'I')
                            # end check
                    else:
                        logmsg.update("Error during parsing result.", 'D')
                logmsg.update(
                    "Current temperature in " + str(city) + " is " + str(temp) + ", humidity " + str(humidity) +
                    "%", 'I')

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
    """
    :param temp: int, temperature
    :param t: list, temperature min, max range
    :param r: list, min, max for exp()
    :param w: list, target range, min max
    :param test: boolean, test for range violation
    :return: int, mapped value
    """
    if test:
        if temp < t[0]:
            temp = t[0]
        elif temp > t[1]:
            temp = t[1]

    a = _scale(temp, t, r)
    b = int(_scale(exp(a), (exp(r[0]), exp(r[1])), w))

    return b
