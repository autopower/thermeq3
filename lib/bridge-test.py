import logmsg
import bridge2

bridge2.bridgeclient.put("status", "heating")
bridge2.bridgeclient.put("ignore_opened", "34")
bridge2.bridgeclient.put("svpnmw", "75")
bridge2.bridgeclient.put("interval", "90")
bridge2.bridgeclient.put("autoupdate", "True")
bridge2.bridgeclient.put("ignore_opened", "34")
bridge2.bridgeclient.put("error", "0")
bridge2.bridgeclient.put("total_switch", "150")
bridge2.bridgeclient.put("uptime", "0")
bridge2.bridgeclient.put("valve_pos", "36")
bridge2.bridgeclient.put("mode", "auto")
bridge2.bridgeclient.put("ignored", "{}")
bridge2.bridgeclient.put("profile", "time")
bridge2.bridgeclient.put("beta", "YES")
bridge2.bridgeclient.put("preference", "per")
bridge2.bridgeclient.put("totalerrors", "0")
bridge2.bridgeclient.put("app_uptime", "0:00:06")
bridge2.bridgeclient.put("command", "")
bridge2.bridgeclient.put("no_oww", "0")
bridge2.bridgeclient.put("valves", "2")

logmsg.start("d:/root/test2.log")
# bridge2.save("d:/root/test2.bridge")
data = bridge2.load("D:/root/test2.bridge")
print data["status"]
