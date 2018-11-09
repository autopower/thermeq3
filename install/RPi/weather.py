import urllib
import urllib2
import logmsg
import traceback
from math import exp
import json
import bridge


def get_weather(mode, data):
    """
    Get current weather for var.situation variable
    :param mode: string, mode "yahoo", "owm" or "local"
    :param data: dictionary
    :return:
    """
    if mode == "LOCAL":
        result = local_weather()
    elif mode == "OWM":
        result = owm_weather(data["owm_id"], data["owm_api_key"])
    else:
        result = yahoo_weather(data["woe_id"])
    logmsg.update(
        "Current temperature in " + str(result["city"]) + " is " + str(result["current_temp"]) + ", humidity " +
        str(result["humidity"]) + "%", 'I')
    return result


def yahoo_weather(woe_id):
    """
    Returns weather from yahoo weather from given WOEID
    :param woe_id: integer, yahoo weather ID
    :return: dictionary, {"current_temp": temp, "city": city, "humidity": humidity}
    """
    city, temp, humidity = "Error city", None, None

    if woe_id is None:
        logmsg.update("Wrong WOEID! Please set WOEID in config file.", 'E')
    else:
        # please change u='c' to u='f' for fahrenheit below
        base_url = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = "select * from weather.forecast where woeid=" + str(woe_id) + " and u='c'"
        yql_url = base_url + urllib.urlencode({'q': yql_query}) + "&format=json"

        try:
            data = json.loads(urllib2.urlopen(yql_url).read())
        except Exception, error:
            logmsg.update("Yahoo communication error: " + str(error), 'E')
            logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
        else:
            if data is not None:
                try:
                    city = data["query"]["results"]["channel"]["location"]["city"]
                    temp = float(data["query"]["results"]["channel"]["item"]["condition"]["temp"])
                    humidity = int(data["query"]["results"]["channel"]["atmosphere"]["humidity"])
                except Exception:
                    pass

    return {
        "current_temp": temp,
        "city": city,
        "humidity": humidity
    }


def owm_weather(owm_id, owm_api_key):
    """
    Returns weather from OWM weather from given OWMID
    :param owm_id: location ID
    :param owm_api_key:
    :return: dictionary, {"current_temp": temp, "city": city, "humidity": humidity}
    """
    city, temp, humidity = "Error city", None, None

    if owm_id is None:
        logmsg.update("Wrong WOEID! Please set WOEID in config.py.", 'E')
    elif owm_api_key is None:
        logmsg.update("OWM API key not set!", 'E')
    else:
        # and check if yahoo is correct
        url = "http://api.openweathermap.org/data/2.5/weather?id=" + str(owm_id) + "&appid=" + \
              owm_api_key + "&units=metric"
        try:
            result = json.load(urllib2.urlopen(url))
        except Exception, error:
            logmsg.update("OWM communication error: " + str(error), 'E')
            logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
        else:
            if "main" in result:
                temp = float(result["main"]["temp"])
                city = result["name"]
                humidity = int(result["main"]["humidity"])
            else:
                logmsg.update("Error during parsing result.", 'D')
        logmsg.update(
            "Current temperature in " + str(city) + " is " + str(temp) + ", humidity " + str(humidity) + "%", 'I')

    return {
        "current_temp": temp,
        "city": city,
        "humidity": humidity
    }


def local_weather():
    """
    Get local temp and humidity from bridge, bridge values are update manually by external app or user!!!
    :return:
    """
    return {
        "current_temp": float(bridge.try_read("lt")),
        "city": "local",
        "humidity": float(bridge.try_read("lh"))
    }


def weather_for_woeid(woeid, owm_id, owm_api_key):
    """
    Returns weather from yahoo weather from given WOEID
    :param owm_id:
    :param owm_api_key:
    :param woeid: integer, yahoo weather ID
    :return: dictionary, {"current_temp": temp, "city": city, "humidity": humidity}
    """
    city = "Error city"
    temp = None
    humidity = None

    if woeid is None or owm_id is None:
        logmsg.update("Wrong WOEID! Please set WOEID in config.py.", 'E')
    elif owm_api_key is None:
        logmsg.update("OWM API key not set!", 'E')
    else:
        # please change u='c' to u='f' for fahrenheit below
        base_url = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
        yql_url = base_url + urllib.urlencode({'q': yql_query}) + "&format=json"

        try:
            data = json.loads(urllib2.urlopen(yql_url).read())
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
                    url = "http://api.openweathermap.org/data/2.5/weather?id=" + str(owm_id) + "&appid=" + \
                          owm_api_key + "&units=metric"
                    try:
                        result = json.load(urllib2.urlopen(url))
                    except Exception, error:
                        logmsg.update("OWM communication error: " + str(error), 'E')
                        logmsg.update("Traceback: " + str(traceback.format_exc()), 'E')
                    else:
                        if "main" in result:
                            owm_temp = round(result["main"]["temp"])
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

