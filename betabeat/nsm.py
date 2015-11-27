#!/usr/bin/env python
import sys
import socket
import base64
import time
import datetime
import os
import errno
import smtplib
import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import urllib
import urllib2
import hashlib
import httplib
import struct
import json
sys.path.insert(0, "/usr/lib/python2.7/bridge/")
from bridgeclient import BridgeClient
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from ast import literal_eval
from math import exp


class setup(object):
	def __init__(self):
		self.version = 144
		self.appStartTime = time.time()
		# window ignore time
		self.window_ignore_time = 30
		self.cw = {
			#
			# required values, if any error in bridge then defaults is used [1]
			#
			# thermeq3 mode, auto or manual
			"mode": ["mode", "auto"],
			# valve position in % to start heating
			"valve": ["valve_pos", 35],
			# start heating if single valve position in %, no matter how many valves are needed to start to heating
			"svpnmw": ["svpnmw", 75],
			# how many valves must be in position stated above
			"valves": ["valves", 2],
			# if in total mode, sum of valves position to start heating
			"total": ["total_switch", 150],
			# preference, "per" = per valve, "total" to total mode
			"pref": ["preference", "per"],
			# interval, seconds to read MAX!Cube
			"int": ["interval", 90],
			# 
			"ign_op": ["ignore_opened", self.window_ignore_time],
			# use autoupdate function?
			"au": ["autoupdate", True],
			# beta features on (yes) or off (no)
			"beta": ["beta", "no"],
			# profile type, time or temp, temp profile type means that external temperature (yahoo weather) is used 
			"profile": ["profile", "time"],
			"no_oww": ["no_oww", 0],
			#
			# optional values
			#
			"ht": ["heattime", {"total": [0, 0.0], datetime.datetime.date(datetime.datetime.now()).strftime("%d-%m-%Y"): [0, time.time()]}],
			# communication errors, this states how many times failed communication between thermeq3 and MAX!Cube, cleared after sending status
			"errs": ["error", 0],
			# same as above, but cumulative number
			"terrs": ["totalerrors", 0],
			"cmd": ["command", ""],
			"msg": ["msg", ""],
			"uptime": ["uptime", ""],
			"appuptime": ["app_uptime", 0],
			"htstr": ["heattime_string", str(datetime.timedelta(seconds=0))],
			"daily": ["daily", ""],
			"status": ["status", "defaults"],
			"cur": ["current_status", "{}"]}
		# status messages
		self.statusMsg = {
			"idle": "idle",
			"heat": "heating",
			"start": "starting",
			"dead": "dead",
			"hv": "heating and ventilating",
			"iv": "idle and ventilating"}
		# my IP address
		self.myip = "127.0.0.1"
		# sd card or usb key mount point, default is /mnt/sda1/
		self.place = ""
		# where is stderr log located, def stp.place+stp.devname+"_error.log"
		self.stderr_log = ""
		# dictionaries for MAX
		self.maxid = {"sn": "000000", "rf": "", "fw": ""}
		self.valves = {}
		self.rooms = {}
		self.devices = {}
		# update this to your location, yahoo WOEID
		self.location = 818717
		# difference from last known valve value, in %
		self.percentage = 3
		# github location for auto update
		self.github = "https://raw.github.com/autopower/thermeq3/master/"
		# home directory is /root
		self.homedir = "/root/"
		# abnormal count of warning is
		self.abnormalCount = 30
		# stp.stderr_log = stp.place + stp.devname + "_error.log"
		self.stderr_log = ""
		# how many windows must be open to recognize that we are ventilating
		self.ventilate_num = 3
		""" this is in config.py file, here just for set type """
		self.max_ip = ""
		self.fromaddr = ""
		self.toaddr = ""
		self.mailserver = ""
		self.mailport = 25
		self.frompwd = ""
		self.devname = ""
		self.timeout = 10
		self.extport = 80

	def initIntervals(self):
		# threshold in seconds, so 10 minutes are 10*60 seconds
		# interval as "name": [interval=how often check, mute int, next_time]
		tm = time.time()
		self.intervals = {
			"max": [120, 0, tm],
			"upg": [4 * 60 * 60, 0, tm],
			"var": [10 * 60, 0, tm],
			# threshold, send every X, muted for X
			"oww": [15 * 60, 45 * 60, 45 * 60],
			# threshold, muted for X, time.time(), trust me, if you don't have access to thermostat you'll kill thermeq for 15*60 :)
			"wrn": [6 * 60 * 60, 24 * 60 * 60, tm],
			"err": [0, 0, 0.0],
			# just sleep value, always calculated as max[0] / slp[1]
			"slp": [40, 3, 0]}
		# day windows/intervals
		# day = [0-from_str, 1-to_str, 2-total or per, 3-mode ("total"/"per"), 4-check interval, 5-valves]
		self.day = [
			["00:00", "06:00", 35, "per", 240, 1],
			["06:00", "10:00", 36, "per", 120, 1],
			["10:00", "14:00", 30, "per", 120, 2],
			["14:00", "22:00", 36, "per", 120, 1],
			["22:00", "23:59", 35, "per", 120, 1]]
		# temperature table
		self.temp = [
			[-30, -20, 20, "per",  90, 2],
			[-20, -10, 25, "per", 120, 2],
			[-10,   0, 28, "per", 120, 2],
			[  0,  10, 30, "per", 180, 2],
			[ 10,  20, 40, "per", 240, 2],					
		]          

	def initPaths(self):
		self.log_filename = self.place + self.devname + ".log"
		self.csv_log = self.place + self.devname + ".csv"
		self.bridgefile = self.place + self.devname + ".bridge"
		self.secweb = {
			"status": str(self.place + "www/status.xml"),
			"owl": str(self.place + "www/owl.xml"),
			"nice": str(self.place + "www/nice.html")}


class variables(object):
	def __init__(self):
		# heat times; total: [totalheattime, time.time()]
		self.ht = {"total": [0, 0.0]}
		# device log, used to count if valve position didn't change
		self.dev_log = {}
		# message queue
		self.msgQ = []
		# initialize bridge
		self.value = BridgeClient()
		# open window dictionary
		self.d_W = {}
		# which mode is selected
		self.selectedMode = "TIME"
		# index in mode table
		self.actModeIndex = -1
		# dictionary for ignoring valves after closing window
		self.d_ignore = {}
		# variable for weather situation
		self.sit = {
			"current_condition": "",
			"current_temp": "0",
			"forecasts": "",
			"title": "title",
			"humidity": "50",
			"city": "city"
		}
		# CSV file
		self.csv = None
		# number of readings when we heating
		self.heatReadings = 0
		# heating is off
		self.heating = False
		# clear errors
		self.err2Clear = False
		self.err2LastStatus = False
		self.error = False


def redirErr(onoff):
	if onoff:
		stp.stderr_log = stp.place + stp.devname + "_error.log"
		try:
			var.ferr = open(stp.stderr_log, "a")
		except Exception:
			raise
		else:
			var.original_stderr = sys.stderr
			sys.stderr = var.ferr
			print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection active"
	else:
		print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection closed"
		sys.stderr = var.original_stderr
		var.ferr.close()


def llError(err_string):
	try:
		err_file = open("/root/nsm.error", "a")
	except Exception:
		print "Error writing to error file!"
		print err_string
	else:
		err_file.write(time.strftime("%H:%M:%S", time.localtime()) + "\t" + err_string + "\r\n")
		err_file.close()


# helpers
def rCW(cw):
	""" returns command word, always string """
	if cw in stp.cw:
		return str(stp.cw[cw][0])
	else:
		return "wrong_key"


def secWebFile(cw, txt):
	""" saves txt to file which is in secondary web directory """
	try:
		fn = str(stp.secweb[str(cw)])
	except Exception:
		var.logger.error("Wrong cw [" + str(cw) + "] for saving file!")
	else:
		try:
			sf = open(fn, "w")
		except Exception:
			var.logger.error("Error writing to file " + fn + "!")
		else:
			sf.write(str(txt))
			sf.close()


def is_private(lookup):
	""" returns True if IP address is private, False if not """
	f = struct.unpack('!I', socket.inet_pton(socket.AF_INET, lookup))[0]
	private = (
		[2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0   http://tools.ietf.org/html/rfc3330
		[3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0 http://tools.ietf.org/html/rfc1918
		[2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0 http://tools.ietf.org/html/rfc1918
		[167772160, 4278190080],  # 10.0.0.0,    255.0.0.0   http://tools.ietf.org/html/rfc1918
	)
	for net in private:
		if (f & net[1] == net[0]):
			return True
	return False


def getPublicIP():
	""" gets public IP, using service at ip.42.pl/raw address """
	try:
		stp.myip = str(urllib2.urlopen('http://ip.42.pl/raw').read())
		tmp = 1
	except Exception:
			try:
				stp.myip = socket.gethostbyname(socket.gethostname())
				tmp = 0
			except Exception:
				tmp = 0xFF
	return tmp


def hexify(tmpadr):
	""" returns hexified address """
	return "".join("%02x" % ord(c) for c in tmpadr).upper()


def getHash(filename):
	checksum = hashlib.md5()
	if os.path.isfile(filename):
		f = file(filename, "rb")
		while True:
			part = f.read(1024)
			if not part:
				break
			checksum.update(part)
		f.close()
	return checksum


def getUptime():
	with open("/proc/uptime", "r") as f:
		uptime_seconds = float(f.readline().split()[0])
		return str(datetime.timedelta(seconds=uptime_seconds)).split(".")[0]


def incErr():
	tmp = tryRead("errs", 0, False)
	var.value.put(rCW("errs"), str(tmp + 1))


def queueMsg(msg):
	var.logger.debug("Queqing [" + str(msg) + "]")
	var.msgQ.insert(0, msg)
	while len(var.msgQ) > 0:
		var.logger.debug("Message queue=" + str(var.msgQ))
		while not str(var.value.get(rCW("msg"))) == "":
			time.sleep(stp.timeout)
		tosend = var.msgQ.pop()
		var.logger.debug("Sending message [" + str(tosend) + "]")
		if tosend == "E":
			var.error = True
			var.err2Clear = True
		elif tosend == "C":
			var.err2Clear = False
			var.err2LastStatus = True
			var.logger.info("Clearing error LED")
		elif tosend == "R":
			saveBridge()
		var.value.put(rCW("msg"), str(tosend))


def getCMD():
	localcmd = var.value.get(rCW("cmd"))
	if localcmd is None:
		return ""
	elif len(localcmd) > 0:
		var.value.put(rCW("cmd"), "")
		var.logger.info("Received command: [" + localcmd + "]")
	return localcmd


def tryRead(cw, default, save):
	if type(default) is str:
		isNum = False
	else:
		isNum = True
	lcw = rCW(cw)

	tmp_str = var.value.get(lcw)

	if tmp_str == "None":
		tmp = default
	else:
		if isNum:
			try:
				tmp = int(tmp_str)
			except Exception:
				tmp = default
		else:
			tmp = tmp_str
	if save:
		var.value.put(lcw, str(tmp))
	return tmp


def readlines(sock, recv_buffer=4096, delim="\r\n"):
	buffer = ""
	data = True
	while data:
		try:
			data = sock.recv(recv_buffer)
			buffer += data
			while buffer.find(delim) != -1:
				line, buffer = buffer.split("\n", 1)
				yield line
		except socket.timeout:
			return
	return


def updateUptime():
	tmp = time.time()
	var.value.put(rCW("uptime"), str(getUptime()))
	var.value.put(rCW("appuptime"), str(datetime.timedelta(seconds=int(tmp - stp.appStartTime))))


def updateAllTimes():
	updateUptime()
	updateCounters(False)


def updateStatus(statusMsg):
	var.value.put(rCW("status"), str(stp.statusMsg[statusMsg]))


def composeMessage(m_subject, m_body):
	c_msg = MIMEMultipart()
	c_msg["From"] = "\"" + stp.devname + "\" <" + stp.fromaddr + ">"
	c_msg["To"] = ', '.join(stp.toaddr)
	c_msg["Subject"] = m_subject
	body = """<html><body><font face="arial,sans-serif">""" + m_body + "</p></body></html>"
	c_msg.attach(MIMEText(body, "html"))

	return c_msg


def checkVar():
	if stp.valve_num > len(stp.valves):
		var.logger.error("You have only " + str(len(stp.valves)) + 
			" valves, but you want to " + str(stp.valve_num) + " of them be checked to turn on heating!")
		stp.valve_num = len(stp.valves)
	if stp.valve_switch > 90:
		var.logger.error("Valve switch position over 90%!")
		stp.valve_switch = 90
	if stp.svpnmw > 100:
		var.logger.error("Single valve switch position over 100%!")
		stp.svpnmw = 100
	if stp.valve_switch > stp.svpnmw:
		var.logger.error("svpnmw (" + str(stp.svpnmw) + 
			"%) is less or equal to valve switch setup (" + str(stp.valve_switch) + "%)!")
		stp.svpnmw = stp.valve_switch		


def sendEmail(sendTxt):
	try:
		server = smtplib.SMTP(stp.mailserver, stp.mailport)
	except Exception, error:
		var.logger.error("Error connecting to mail server " + str(stp.mailserver) + ":" + str(stp.mailport) + ". Error code: " + str(error))
		var.logger.error("Traceback: " + str(traceback.format_exc()))
	else:
		try:
			server.ehlo()
			if server.has_extn('STARTTLS'):
				server.starttls()
				server.ehlo()
			server.login(stp.fromaddr, stp.frompwd)
			server.sendmail(stp.fromaddr, stp.toaddr, sendTxt)
		except smtplib.SMTPAuthenticationError:
			var.logger.error("Authentification error during sending email.")
		except Exception, error:
			var.logger.error("Error during sending email. Error code: " + str(error))
		else:
			server.quit()
			var.logger.info("Mail was sent.")
			return 0
	return 1


def saveBridge():
	try:
		f = open(stp.bridgefile, "w")
	except Exception:
		var.logger.error("Error writing to bridgefile!")
	else:
		for k, v in stp.cw.iteritems():
			try:
				tmp = var.value.get(v[0])
			except Exception:
				tmp = ""
			if tmp == "None" or tmp is None:
				tmp = str(v[1])
			f.write(v[0] + "=" + str(tmp) + "\r\n")
		f.close()
		var.logger.debug("Bridge file saved.")


def loadBridge():
	if os.path.exists(stp.bridgefile):
		with open(stp.bridgefile, "r") as f:
			# create dictionary from codewords setup dictionary
			cw = {}
			for k in stp.cw.iteritems():
				cw.update({k[1][0]: k[1][1]})
			for line in f:
				t = (line.rstrip("\r\n")).split('=')
				if t[0] == rCW("ht"):
					try:
						var.ht = literal_eval(t[1])
					except Exception:
						var.ht = {"total": [0, 0.0]}
				else:
					if t[0] in cw:
						# check if correct values are loaded						
						if t[1] == "" or t[1] is None:
							defValue = str(cw[t[0]])
							var.logger.info("CW [" + str(t[0]) + "] empty, using default [" + str(t[1]) + "]")
							var.value.put(t[0], defValue)
						else:
							var.value.put(t[0], t[1])
					else:
						var.logger.error("Bridge error codeword @[" + str(t[0]) + "] value [" + str(t[1]) + "]")
			f.close()
		var.logger.debug("Bridge file loaded.")
		updateAllTimes()
	else:
		for k, v in stp.cw.iteritems():
			var.value.put(v[0], v[1])
		var.logger.error("Error loading bridge file, using defaults!")


# problem prediction routines, if during heating valve didn't change position, something is wrong
def isSame(key):
	tmp = var.dev_log[key][1]
	kv = stp.valves[key][1]
	if kv >= tmp - stp.percentage and kv <= tmp + stp.percentage:
		return True
	else:
		return False


def doDevLogging():
	for k, v in stp.valves.iteritems():
		if k in var.dev_log:
			if var.heating and isSame(k):
				var.dev_log[k][0] += 1
			var.dev_log[k][1] = v[0]
		else:
			var.dev_log.update({k: [0, v[0]]})


# autoupdate routines
def downloadFile(filename):
	errstr = ""
	try:
		request = urllib2.urlopen(stp.github + filename)
		response = request.read()
	except urllib2.HTTPError, e:
		errstr += "HTTPError = " + str(e.reason)
	except urllib2.URLError, e:
		errstr += "URLError = " + str(e.reason)
	except httplib.HTTPException, e:
		errstr += "HTTPException"
	except Exception, e:
		errstr += "Exception = " + str(traceback.format_exc())
	else:
		fbase = filename.split(".")[0]
		try:
			f = file(stp.homedir + fbase + ".upd", "wb")
		except Exception, e:
			errstr = "Problem during saving new version. File: " + stp.homedir + fbase + ". Error: " + str(e) + " Traceback: " + str(traceback.format_exc())
		else:
			f.write(response)
			f.close()
			errstr = ""

	if not errstr == "":
		var.logger.error(errstr)
		return False
	request.close()
	return True


def checkUpdate():
	errstr = "Unable to get latest version info - "
	try:
		request = urllib2.urlopen(stp.github + "autoupdate.data")
		response = request.read().rstrip("\r\n")
	except urllib2.HTTPError, e:
		errstr += "HTTPError = " + str(e.reason)
	except urllib2.URLError, e:
		errstr += "URLError = " + str(e.reason)
	except httplib.HTTPException, e:
		errstr += "HTTPException"
	except Exception, e:
		errstr += "Exception = " + str(traceback.format_exc())
	else:
		errstr = ""
		t = response.split(":")

		new_hash = getHash(stp.homedir + str(t[1])).hexdigest()
		if new_hash == "":
			var.logger.error("Can't find file " + str(t[1]))
		else:
			try:
				tmp_ver = int(t[0])
			except Exception, e:
				tmp_ver = 0
			var.logger.debug("Available file: " + str(t[1]) + ", V" + str(tmp_ver) + " with hash " + str(t[3]))
			var.logger.debug("Actual version: " + str(stp.version) + ", hash: " + str(new_hash))
			if new_hash != t[3] and stp.version <= tmp_ver:
				var.logger.info("Downloading new version V" + str(tmp_ver))
				down_result = downloadFile(t[1])
				if down_result:
					var.logger.info("V" + str(tmp_ver) + " downloaded. Hash is " + str(t[3]))
					return 2
				else:
					var.logger.error("Problem downloading new version. Result=" + str(down_result) + ", file=" + str(t[1]))
			else:
				return 1

	if not errstr == "":
		var.logger.error(errstr)
	return 0


def doUpdate():
	chk = checkUpdate()
	if stp.au:
		if chk == 2:
			os.rename(stp.homedir + "nsm.upd", stp.homedir + "nsm.py")
			temp_key = stp.maxid["sn"]
			body = """<h1>Device upgrade information.</h1>
			<p>Hello, I'm your thermostat and I have a information for you.<br/>
			Please take a note, that I found new version of my control script and I'll be upgraded in few seconds.</br>
			Resistance is futile :).<br/>"""
			sendWarning("upgrade", temp_key, body)
			queueMsg("R")
	else:
		var.logger.info("Auto update is disabled.")


# send this, send that
def sendErrorLog():
	if os.path.getsize(stp.stderr_log) > 0:
		devname = stp.devname
		body = """<h1>%(a0)s status email.</h1>
		<p>Hello, I'm your thermostat and I sending you this email with error logfile as attachment.<br/>""" % \
			{"a0": str(devname)}
		msg = composeMessage(devname + " log email (thermeq3 device)", body)

		part = MIMEBase("application", "octet-stream")
		part.set_payload(open(stp.stderr_log, "rb").read())
		encode_base64(part)
		head, tail = os.path.split(stp.stderr_log)
		part.add_header("Content-Disposition", "attachment; filename=\"" + tail + "\"\"")
		msg.attach(part)

		if sendEmail(msg.as_string()) == 0:
			var.value.put(rCW("errs"), "0")
			var.ferr.close()
			var.ferr = open(stp.stderr_log, "w")
	else:
		var.logger.info("Zero sized stderr log file, nothing'll be send")


def sendStatus():
	devname = stp.devname
	valve_pos = int(var.value.get(rCW("valve")))
	error = int(var.value.get(rCW("errs")))
	status = var.value.get(rCW("status"))
	interval = int(var.value.get(rCW("int")))
	totalerrs = int(var.value.get(rCW("terrs")))

	uptime_string = getUptime()

	var.value.put(rCW("terrs"), str(totalerrs + error))
	heat_str = var.value.get(rCW("htstr"))

	body = """<h1>%(a0)s status email.</h1>
	<p>Hello, I'm your thermostat and I sending you this status email.<br/>
	Actual system status <b>%(a1)s</b> is checked every <b>%(a5)02d</b> seconds
	for valve position of <b>%(a6)02d%%</b>.<br/>
	Total heating time is <b>%(a3)s</b><br/>
	Errors from last status mail: <b>%(a2)s</b><br/>
	Total errors since start: <b>%(a7)d</b><br/>
	Device uptime: <b>%(a8)s</b><br/>
	Application uptime: <b>%(a9)s</b><br/>""" % \
		{'a0': str(devname),
			'a1': status,
			'a2': str(error),
			'a3': heat_str,
			'a5': interval,
			'a6': valve_pos,
			'a7': totalerrs,
			'a8': uptime_string,
			'a9': str(datetime.timedelta(seconds=int(time.time() - stp.appStartTime)))}

	msg = composeMessage(devname + " status email (thermeq3 device)", body)

	if sendEmail(msg.as_string()) == 0:
		var.value.put(rCW("errs"), "0")


def silence(key, isWin):
	#
	# d_w = key: OW_time(thisnow), isMuted(False), warning/error count(0)
	#
	# is there key in dict?
	dt = datetime.datetime.now()
	if key not in var.d_W:
		# there no key, so its new warning
		var.logger.debug("No key " + str(key) + " in d_W. Key added.")
		if isWin:
			var.d_W.update({key: [stp.devices[key][5], False, 0]})
		else:
			var.d_W.update({key: [dt, False, 0]})
		return 2
	else:
		# yes, there it is, so check if we are silent, if so exit, otherwise reset mute
		# threshold, send every X, muted for X
		# "oww": [10*60, 30*60, 45*60]
		# threshold, muted for X, time.time()
		# "wrn": [60*60, 60*60, tm]
		if var.d_W[key][1]:
			# yes, we must be silent
			if isWin:
				tmp = var.d_W[key][0] + datetime.timedelta(seconds=stp.intervals["oww"][2])
			else:
				tmp = var.d_W[key][0] + datetime.timedelta(seconds=stp.intervals["wrn"][1])
			if tmp < dt:
				return 1
			else:
				# silence is over
				var.d_W[key][1] = False

	# increment warning counter for this key
	var.d_W[key][2] += 1
	if var.d_W[key][2] > stp.abnormalCount:
		var.logger.critical("Abnormal count of warnings for device [" + str(key) + "], name [" + str(stp.devices[key][2]) + "]")
		var.d_W[key][2] = 0
	return 0


def itsWarnTime():
	tm = time.time()
	if tm > stp.intervals["wrn"][2]:
		stp.intervals["wrn"][2] = tm + stp.intervals["wrn"][0]
		return True
	else:
		return False


def sendWarning(selector, dev_key, body_txt):
	devname = stp.devname
	subject = ""
	if selector != "openmax" and selector != "upgrade":
		d = stp.devices[dev_key]
		dn = d[2]
		r = d[3]
		rn = stp.rooms[str(r)]
	sil = silence(dev_key, selector == "window")
	if sil == 1:
		var.logger.debug("Warning for device " + str(dev_key) + " is muted!")
		return

	mutestr = "http://" + stp.myip + ":" + str(stp.extport) + "/data/put/command/mute" + str(dev_key)

	if selector == "window":
		owd = int((datetime.datetime.now() - stp.devices[dev_key][5]).total_seconds())
		oww = int((datetime.datetime.now() - var.d_W[dev_key][0]).total_seconds())
		if sil == 0 and oww < stp.intervals["oww"][1]:
			return
		subject = "Open window in room " + str(rn[0]) + ". Warning from " + devname + " (thermeq3 device)"
		body = """<h1>Device %(a0)s warning.</h1>
		<p>Hello, I'm your thermostat and I have a warning for you.<br/>
		Please take a care of window <b>%(a0)s</b> in room <b>%(a1)s</b>.
		Window in this room is now opened more than <b>%(a2)d</b> mins.<br/>
		Threshold for warning is <b>%(a3)d</b> mins.<br/>
		</p><p>You can <a href="%(a4)s">mute this warning</a> for %(a5)s mins.""" % \
			{'a0': str(dn),
				'a1': str(rn[0]),
				'a2': int(owd / 60),
				'a3': int(stp.intervals["oww"][0] / 60),
				'a4': str(mutestr),
				'a5': int(stp.intervals["oww"][2] / 60)}
	else:
		if sil == 0 and not rightTime("wrn"):
			return
		if selector == "battery":
			subject = "Battery status for device " + str(dn) + ". Warning from " + devname + " (thermeq3 device)"
			body = """<h1>Device %(a0)s battery status warning.</h1>
			<p>Hello, I'm your thermostat and I have a warning for you.<br/>
			Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
			This device have low batteries, please replace batteries.<br/>
			</p><p>You can <a href="%(a2)s">mute this warning</a> for %(a3)s mins.""" % \
				{'a0': str(dn),
					'a1': str(rn[0]),
					'a2': str(mutestr),
					'a3': int(stp.intervals["wrn"][1] / 60)}
		elif selector == "error":
			subject = "Error report for device " + str(dn) + ". Warning from " + devname + " (thermeq3 device)"
			body = """<h1>Device %(a0)s radio error.</h1>
			<p>Hello, I'm your thermostat and I have a warning for you.<br/>
			Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
			This device reports error.<br/>
			</p><p>You can <a href="%(a2)s">mute this warning</a> for %(a3)s mins.""" % \
				{'a0': str(dn),
					'a1': str(rn[0]),
					'a2': str(mutestr),
					'a3': int(stp.intervals["wrn"][1] / 60)}
		elif selector == "openmax":
			subject = "Can't connect to MAX! Cube! Warning from " + devname + " (thermeq3 device)"
			body = body_txt
		elif selector == "upgrade":
			subject = devname + " (thermeq3 device) is going to be upgraded"
			body = body_txt

	msg = composeMessage(subject, body)

	if sendEmail(msg.as_string()) == 0 and selector == "window":
		var.d_W[dev_key][0] = datetime.datetime.now()


# logging etc
def startLog():
	""" opens log file """
	var.logger = logging.getLogger("thermeq3")
	var.logger.setLevel(logging.DEBUG)

	# var.fh = logging.FileHandler(stp.log_filename)
	var.fh = TimedRotatingFileHandler(stp.log_filename, when="W0", interval=4, backupCount=12)
	var.fh.setLevel(logging.DEBUG)

	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
	var.fh.setFormatter(formatter)
	var.logger.addHandler(var.fh)

	var.logger.info("--> V" + str(stp.version) + " started with PID=" + str(os.getpid()) + " <--")


def exportCSV(onoff):
	if onoff == "init":
		if os.path.exists(stp.csv_log):
			os.rename(stp.csv_log, stp.place + stp.devname + "_" + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".csv")
		try:
			var.csv = open(stp.csv_log, "a")
		except Exception:
			raise
		else:
			for k, v in stp.valves.iteritems(): 		
				# to get headers like rooma name - valve name use this (uncomment)
				# room_id = str(getName(k)[0]) 
				# name = rooms[room_id][0] + "-" + stp.devices[k][2]
				# and comment line below
				name = stp.devices[k][2]
				var.csv.write(name + "," + name + ",")
			var.csv.write("\r\n")
	elif onoff == "close":
		try:
			var.csv.close()
		except Exception:
			var.logger.error("Can't close CSV file!")


# EQ-3/ELV MAX! communication
def openMAX():
	""" open communication to MAX! Cube """
	var.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# on some system use code below:
	# var.client_socket.setblocking(0)
	var.client_socket.settimeout(int(stp.timeout / 2))
	temp_key = stp.maxid["sn"]

	i = 0
	while i < 3:
		try:
			var.client_socket.connect((stp.max_ip, 62910))
		except Exception, e:
			incErr()
			i = i + 1
			time.sleep(int(stp.timeout / 2))
		else:
			i = 3
			if temp_key in var.d_W:
				var.logger.debug("Key " + str(temp_key) + " in d_W deleted.")
				del var.d_W[temp_key]
			return True

	var.logger.error("Error opening connection to MAX Cube. Error: " + str(e))
	var.logger.error("Traceback: " + str(traceback.format_exc()))
	body = """<h1>Device %(a0)s warning.</h1>
	<p>Hello, I'm your thermostat and I have a warning for you.<br/>
	Please take a care of connection to MAX! Cube.</br>
	I can't connect to Cube at address <b>%(a1)s</b>.<br/>
	Error: %(a2)s<br/>
	Traceback: %(a3)s<br/>""" % \
		{'a0': str(stp.devname),
			'a1': str(stp.max_ip),
			'a2': str(e),
			'a3': str(traceback.format_exc())}
	sendWarning("openmax", temp_key, body)
	return False


def setIgnoredValves(key):
	room = stp.devices[key][3]
	for k, v in stp.devices.iteritems():
		# this is heating thermostat and is in room where we want ignore all heating thermostats and is not in d_ignore dictionary
		# it means, is not ignored now
		if v[0] == 1 and v[3] == room and k not in var.d_ignore:
			# don't heat X*60 seconds after closing window
			var.d_ignore.update({k: time.time() + var.ignore_time * 60})
			var.logger.debug("Ignoring valve " + str(k) + " until " + time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(var.d_ignore[k])))


def maxCmd_H(line):
	""" process H response """
	stp.maxid["sn"] = line[0]
	stp.maxid["rf"] = line[1]
	stp.maxid["fw"] = line[2]


def maxCmd_M(line, refresh):
	""" process M response """
	es = base64.b64decode(line[2])
	room_num = ord(es[2])
	es_pos = 3
	this_now = datetime.datetime.now()
	for i in range(0, room_num):
		room_id = str(ord(es[es_pos]))
		room_len = ord(es[es_pos + 1])
		es_pos += 2
		room_name = es[es_pos:es_pos + room_len]
		es_pos += room_len
		room_adr = es[es_pos:es_pos + 3]
		es_pos += 3
		if room_id not in stp.rooms or refresh:
			# 					id   :0room_name, 1room_address,   2is_win_open
			stp.rooms.update({room_id: [room_name, hexify(room_adr), False]})
	dev_num = ord(es[es_pos])
	es_pos += 1
	for i in range(0, dev_num):
		dev_type = ord(es[es_pos])
		es_pos += 1
		dev_adr = hexify(es[es_pos:es_pos + 3])
		es_pos += 3
		dev_sn = es[es_pos:es_pos + 10]
		es_pos += 10
		dev_len = ord(es[es_pos])
		es_pos += 1
		dev_name = es[es_pos:es_pos + dev_len]
		es_pos += dev_len
		dev_room = ord(es[es_pos])
		es_pos += 1
		if dev_adr not in stp.devices or refresh:
			#                            0type     1serial 2name     3room    4OW,5OW_time, 6status, 7info, 8temp offset
			stp.devices.update({dev_adr: [dev_type, dev_sn, dev_name, dev_room, 0, this_now, 0, 0, 7]})


def maxCmd_C(line):
	""" process C response """
	es = base64.b64decode(line[1])
	if ord(es[0x04]) == 1:
		dev_adr = hexify(es[0x01:0x04])
		stp.devices[dev_adr][8] = es[0x16]


def maxCmd_L(line):
	""" process L response """
	es = base64.b64decode(line[0])
	es_pos = 0
	while (es_pos < len(es)):
		dev_len = ord(es[es_pos]) + 1
		valve_adr = hexify(es[es_pos + 1:es_pos + 4])
		valve_status = ord(es[es_pos + 0x05])
		valve_info = ord(es[es_pos + 0x06])
		valve_temp = 0xFF
		valve_curtemp = 0xFF
		# WallMountedThermostat (dev_type 3)
		if dev_len == 13:
			if valve_info & 3 != 2:
				valve_temp = float(int(hexify(es[es_pos + 0x08]), 16)) / 2  # set temp
				valve_curtemp = float(int(hexify(es[es_pos + 0x0C]), 16)) / 10  # measured temp
		# HeatingThermostat (dev_type 1 or 2)
		elif dev_len == 12:
			valve_pos = ord(es[es_pos + 0x07])
			if valve_info & 3 != 2:
				valve_temp = float(int(hexify(es[es_pos + 0x08]), 16)) / 2
				valve_curtemp = float(ord(es[es_pos + 0x0A])) / 10
			stp.valves.update({valve_adr: [valve_pos, valve_temp, valve_curtemp]})
		# WindowContact
		elif dev_len == 7:
			tmp_open = ord(es[es_pos + 0x06]) & 2
			if tmp_open != stp.devices[valve_adr][4]:
				tmp_txt = "Window contact " + str(stp.devices[valve_adr][2]) + " is now "
				r_id = str(stp.devices[valve_adr][3])
				if tmp_open == 0:
					var.logger.info(tmp_txt + "closed.")
					stp.rooms[r_id][2] = False
					if valve_adr in var.d_W:
						var.logger.debug("Key " + str(valve_adr) + " in d_W deleted.")
						del var.d_W[valve_adr]
					# now check for window closed ignore interval, if non zero set valves to ignore
					if var.ignore_time > 0:
						setIgnoredValves(valve_adr)
				else:
					var.logger.info(tmp_txt + "opened.")
					stp.rooms[r_id][2] = True
				stp.devices[valve_adr][4] = tmp_open
				stp.devices[valve_adr][5] = datetime.datetime.now()
		# save status and info
		stp.devices[valve_adr][6] = valve_status
		stp.devices[valve_adr][7] = valve_info
		es_pos += dev_len


def readMAX(refresh):
	""" read data from MAX! cube """
	var.client_socket.settimeout(int(stp.timeout / 3))
	var.error = False
	for line in readlines(var.client_socket):
		data = line
		sd = data[2:].split(",")
		if data[0] == 'H':
			maxCmd_H(sd)
		elif data[0] == 'M':
			maxCmd_M(sd, refresh)
		elif data[0] == 'C':
			maxCmd_C(sd)
		elif data[0] == 'L':
			maxCmd_L(sd)


def closeMAX():
	""" close connection to MAX """
	var.client_socket.close()


# some stupid commands :)
def updateCounters(heatStart):
	# save the date
	nw = datetime.datetime.date(datetime.datetime.now()).strftime("%d-%m-%Y")
	tm = time.time()

	# update total heat counter
	if var.heating:
		tmp = var.ht["total"][0]
		tmp += int(time.time() - var.ht["total"][1])
		var.value.put(rCW("ht"), str(var.ht))
		var.value.put(rCW("htstr"), str(datetime.timedelta(seconds=tmp)))
		var.logger.info("Total heat counter updated to " + str(datetime.timedelta(seconds=tmp)))
		var.ht["total"][0] = tmp
		var.ht["total"][1] = time.time()

	# is there a key for today?
	if nw in var.ht:
		if heatStart:
			var.ht[nw][1] = tm
		elif var.heating:
			totalheat = int(var.ht[nw][0] + (tm - var.ht[nw][1]))
			var.ht[nw] = [totalheat, time.time()]
			var.value.put(rCW("ht"), str(var.ht))
			var.value.put(rCW("daily"), str(datetime.timedelta(seconds=totalheat)))
	else:
		if len(var.ht) > 1:
			# if there a key, this must be old key(s)
			# save the old date, and flush values into log
			for k in var.ht.keys():
				v = var.ht[k]
				if not k == "total":
					var.logger.info(str(k) + " heating daily summary: " + str(datetime.timedelta(seconds=v[0])))
					var.logger.debug("Deleting old daily key: " + str(k))
					del var.ht[k]
			# and close CSV file
			exportCSV("close")
		# create the new key
		var.logger.debug("Creating new daily key: " + str(nw))
		var.ht.update({nw: [0, time.time()]})
		# so its a new day, update other values
		exportCSV("init")
		# day readings warning, take number of heated readings and divide by 2
		drW = var.heatReadings / 2
		var.logger.debug("Day reading warnings value=" + str(drW))
		for k, v in var.dev_log.iteritems():
			var.logger.debug("Valve: " + str(k) + " has value " + str(v[0]))
			if v[0] > drW:
				var.logger.info("Valve: " + str(k) +
							" reports during heating too many same % positions, e.g. " +
							str(v[0]) + " per " + str(drW))
			var.dev_log[k][0] = 0
		var.heatReadings = 0
		saveBridge()


def writeStrings():
	""" construct and write CSV data, Log debug string and current status string """
	if var.heating:
		logstr = "Heating"
	else:
		logstr = "Idle"
	logstr += ", "
	if stp.preference == "per":
		logstr += str(stp.valve_switch) + "%" + " at " + str(stp.valve_num) + " valve(s)."
	elif stp.preference == "total":
		logstr += "total value of " + str(getTotal()) + "."
	var.logger.debug(logstr)
	var.csv.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + "," + str(1 if var.heating else 0) + ",")

	rooms = {}
	current = {}
	for k, v in stp.rooms.iteritems():
		rooms.update({str(v[0]): ["", v[2]]})
		current.update({str(v[0]): {}})

	for k, v in stp.valves.iteritems():
		# update rooms string
		room_id = str(getName(k)[0])
		roomStr = rooms[room_id][0]
		roomStr += "\r\n\t[" + str(k) + "] " + '{:<20}'.format(str(stp.devices[k][2])) + "@" + '{:>3}'.format(str(v[0])) + "% @ " + \
			'{:>4}'.format(str(v[1])) + "'C # " + '{:>4}'.format(str(v[2])) + "'C "
		cv = countValve(k)
		if cv:
			roomStr += "(+)"
		else:
			roomStr += "(-)"

		rooms[room_id][0] = roomStr
		var.csv.write(str(v[0]) + "," + str(v[1]) + ",")

		current[room_id].update({str(k): [str(stp.devices[k][2]), str(v[0]),
			str(v[1]), str(v[2]), str(1 if cv else 0)]})

	var.csv.write("\r\n")

	logstr = "Actual positions follows"
	for k, v in rooms.iteritems():
		logstr += "\r\nRoom: " + str(k)
		if v[1]:
			logstr += ", window opened"
		logstr += str(v[0])
	var.logger.debug(logstr)
	var.csv.flush()

	# second web
	# JSON formated status
	secWebFile("status", current)
	# and bridge variable
	var.value.put(rCW("cur"), str(current))
	# nice text web
	logstr.replace("\r\n", "<br/>")
	logstr.replace("\t", "&#9;")
	secWebFile("nice", "<html>\r\n<title>\r\nStatus</title>\r\n<body>\r\n<p><pre>" +
		logstr + "</pre></p>\r\n</body>\r\n</html>")


def readMAXData(refresh):
	if not openMAX():
		queueMsg("E")
	else:
		readMAX(refresh)
		if not refresh:
			writeStrings()
	closeMAX()


# and here we go, this is app logic
def isWinOpen(key):
	""" Return true if window is open """
	v = stp.devices[key]
	if v[0] == 4 and v[4] == 2:
		return True
	else:
		return False


def isWinOpenTooLong(key):
	""" return True if window open time is > defined warning interval """
	v = stp.devices[key]
	if isWinOpen(key):
		tmp = (datetime.datetime.now() - v[5]).total_seconds()
		if tmp > stp.intervals["oww"][0]:
			return True
		else:
			return False


def isBattError(key):
	v = stp.devices[key]
	if v[7] & 128 == 128:
		return True
	else:
		return False


def isRadioError(key):
	v = stp.devices[key]
	if v[6] & 8 == 8:
		return True
	else:
		return False


def getTotal():
	return stp.total_switch


def getName(k):
	v = stp.valves[k]
	dn = stp.devices[k][2]
	rn = stp.rooms[str(stp.devices[k][3])][0]
	return [rn, dn, v]


def getKeyName(k):
	return {k: getName(k)}


def doheat(heatOrNot):
	if heatOrNot:
		var.ht["total"][1] = time.time()
		queueMsg("H")
		updateStatus("heat")
	else:
		queueMsg("S")
		updateStatus("idle")
	updateCounters(heatOrNot)
	var.heating = heatOrNot


def countValve(key):
	if key in var.d_ignore:
		if var.d_ignore[key] < time.time():
			del var.d_ignore[key]
		else:
			return False
	return True


# day table
def checkDayTable():
	if len(stp.day) > 1:
		for i in range(len(stp.day) - 1):
			# time.strptime(k[0], "%H:%M")
			if time.strptime(stp.day[i + 1][0], "%H:%M") <= time.strptime(stp.day[i][0], "%H:%M"):
				var.logger.error("Day mode table is wrong! Using default table!")
				stp.day = [["00:00", "23:59", 40, 185, "total", 120, 1]]


def doControl():
	# check if variables are set correctly
	checkVar()
	# initialize
	tmp = {}
	open_windows = []

	for k, v in stp.devices.iteritems():
		if v[4] == 2:
			room_id = str(v[3])
			room_name = str(stp.rooms[room_id][0])
			tmp.update({k: room_name})

		if isWinOpenTooLong(k):
			open_windows.append(k)
			var.logger.debug("Warning condition for window " + str(k) + " met")
		if isBattError(k):
			sendWarning("battery", k, "")
		if isRadioError(k):
			sendWarning("error", k, "")

	# check if ventilate and if not then send warning
	if var.no_oww == 0 and len(open_windows) < stp.ventilate_num:
		for idx, k in enumerate(open_windows):
			sendWarning("window", k, "")
	# else check if ventilating and update status
	elif len(open_windows) >= stp.ventilate_num:
		if var.heating:
			updateStatus("hv")
		else:
			updateStatus("iv")

	# second web
	secWebFile("owl", tmp)

	if var.err2Clear and not var.error:
		queueMsg("C")
	if var.err2LastStatus:
		var.err2LastStatus = False
		if var.heating:
			queueMsg("H")
			var.logger.info("Resuming heating state on status LED")
	# var.logger.debug("Control: " + str(var.heating) + "=" + str(heat) + ", " + str(grt) + "; " + str(stp.valve_num) + " , " + str(valve_count))

	# and now showtime
	stp.total = getTotal()
	# grand total
	# heat: 0 = disable, 1 = heat per, 2 = total, 3 = svpnmw
	heat = 0 
	grt = 0
	valve_count = 0
	valve_key = {}

	for k, v in stp.valves.iteritems():
		# if valve is ok to evaluate
		if countValve(k):
			# if preference is per valve
			if stp.preference == "per":
				# and valve position is over single valve position no matter what
				if v[0] > stp.svpnmw:
					heat = 3
				# or valve is over desired position to switch heating on
				elif v[0] > stp.valve_switch:
					valve_count += 1
					if valve_count >= stp.valve_num:
						heat = 1
						valve_key.update(getKeyName(k))
			elif stp.preference == "total":
				grt += v[0]
				if grt >= stp.total:
					heat = 2

	# increment number of readings with heat on
	if heat:
		var.heatReadings += 1

	# var.logger.debug("Control: " + str(var.heating) + "=" + str(heat) + ", " + str(grt) + "; " + str(stp.valve_num) + " , " + str(valve_count))

	if bool(heat) != var.heating:
		if heat > 0:
			txt = "heating started due to"
			if heat == 1 and valve_count >= stp.valve_num:
				for k, v in valve_key.iteritems():
					txt += " room " + str(v[0]) + ", valve " + str(v[1]) + "@" + str(v[2])
			elif heat == 2:
					txt += " sum of valve positions = " + str(grt)
			elif heat == 3:
					txt += " single valve position, no matter what " + str(stp.svpnmw) + "%"
			var.logger.info(txt)
			if tryRead("mode", "auto", True).upper() == "AUTO":
				doheat(True)
		else:
			var.logger.info("heating stopped.")
			if tryRead("mode", "auto", True).upper() == "AUTO":
				doheat(False)
			
	# update status, this was added due to some issues in status update
	if var.heating:
		updateStatus("heat")
	else:
		updateStatus("idle")


# check if its right time to update
def rightTime(what):
	tm = time.time()
	if tm > stp.intervals[what][2]:
		stp.intervals[what][2] = tm + stp.intervals[what][0]
		return True
	else:
		return False


# beta features
def weather_for_woeid(woeid):
	""" returns weather from yahoo weather from given WOEID """
	# please change u='c' to u='f' for farenheit below
	baseurl = "https://query.yahooapis.com/v1/public/yql?"
	yql_query = "select * from weather.forecast where woeid=" + str(woeid) + " and u='c'"
	yql_url = baseurl + urllib.urlencode({'q':yql_query}) + "&format=json"
	
	try:
		result = urllib2.urlopen(yql_url).read()
		data = json.loads(result)
	except Exception, error:
		var.logger.error("Yahoo communication error: "+ str(error))
		var.logger.error("Traceback: " + str(traceback.format_exc()))
		city = "Error city"
		temp = 0
		humidity = 50
	else:
		city = data["query"]["results"]["channel"]["location"]["city"]
		temp = int(data["query"]["results"]["channel"]["item"]["condition"]["temp"]) 
		humidity = int(data["query"]["results"]["channel"]["atmosphere"]["humidity"])
		
		# and check if yahoo is correct, PLEASE USE OWN API KEY!!!
		url = "http://api.openweathermap.org/data/2.5/weather?q=" + str(city) + "&appid=2de143494c0b295cca9337e1e96b00e0"
		try:
			result = json.load(urllib2.urlopen(url))
		except Exception, error:
			var.logger.error("OWM communication error: "+ str(error))
			var.logger.error("Traceback: " + str(traceback.format_exc()))
		else:
			owm_temp = round(result["main"]["temp"] / 100)
			yho_temp = round(temp) 
			if abs(yho_temp / owm_temp) > 0.1:
				var.logger.info("Difference between Yahoo and OWM temperatures. Yahoo=" + str(yho_temp) + \
					" OWM=" + str(owm_temp)) 
		# end check
		var.logger.info("Current temperature in " + str(city) + " is " + str(temp) + ", humidity " + str(humidity) + "%")

 		return {
			"current_temp": temp,
			"city": city,
			"humidity": humidity
		}


def scale(val, src, dst):
	""" Scale the given value from the scale of src to the scale of dst """
	return ((val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]


def interval_scale(temp, t, r, w, test):
	if test:
		if temp < t[0]:
			temp = t[0]
		elif temp > t[1]:
			temp = t[1]

	a = scale(temp, t, r)
	b = int(scale(exp(a), (exp(r[0]), exp(r[1])), w))

	return b


def update_ignores_2sit():
	var.sit = weather_for_woeid(stp.location)
	temp = int(var.sit["current_temp"])

	# modify OWW
	tmr = interval_scale(temp, (-35.0, 35.0), (0, 10), (10, 360), True)
	stp.intervals["oww"] = [tmr * 60, (3 * tmr) * 60, (3 * tmr) * 60]
	var.logger.debug("OWW interval updated to " + str(stp.intervals["oww"]))

	# and now modify valve ignore time
	tmr = interval_scale(temp, (0.0, 35.0), (14, 3.0), (15, 120), False)
	var.ignore_time = stp.window_ignore_time + tmr
	var.value.put(rCW("ign_op"), str(var.ignore_time))
	var.logger.debug("Ignore interval updated to " + str(var.ignore_time))


def time_in_range(start, end, x):
	today = datetime.date.today()
	start = datetime.datetime.combine(today, start)
	end = datetime.datetime.combine(today, end)
	x = datetime.datetime.combine(today, x)
	if end <= start:
		end += datetime.timedelta(1)		# tomorrow!
	if x <= start:
		x += datetime.timedelta(1)			# tomorrow!
	return start <= x <= end


def isTime():
	this_now = datetime.datetime.now().time()
	for k in stp.day:
		nf = datetime.datetime.strptime(k[0], "%H:%M").time()
		nt = datetime.datetime.strptime(k[1], "%H:%M").time()
		if time_in_range(nf, nt, this_now):
			return stp.day.index(k)
	return -1


def setMode(value):
	if value[3] == "total":
		stp.total_switch = value[2]
	else:
		stp.valve_switch = value[2]
	stp.preference = value[3]
	stp.intervals["max"][0] = value[4]
	stp.valve_num = value[5]
	# just sleep value, always calculated as max[0] / slp[1]
	stp.intervals["slp"][0] = int(value[4] / stp.intervals["slp"][1])


def timeMode():
	# day = [0-from_str, 1-to_str, 2-total or per, 3-mode ("total"/"per"), 4-check interval, 5-valves]
	md = isTime()
	if md != -1:
		if md != var.actModeIndex:
			kv = stp.day[md]
			var.actModeIndex = md
			var.logger.debug("Switching day mode to " + str(md) + " = " + str(kv))
			setMode(kv)


def tempMode():
	c_temp = int(var.sit["current_temp"])
	for k in stp.temp:
		kv = stp.temp[k]
		if c_temp >= kv[0] and c_temp < kv[1]:
			var.actModeIndex = k
			var.logger.debug("Switching temp mode to " + str(kv[0]) + " ~ " + str(kv[1]))
			setMode(kv)
			

def doProfiles():
	tmp_prof = tryRead("profile", "time", False).upper()
	if tmp_prof != var.selectedMode:
		var.selectedMode = tmp_prof
		var.actModeIndex = -1		    
	if tmp_prof == "TIME":
		timeMode()
	elif tmp_prof == "TEMP":
		tempMode() 

# beta end


def doLoop():
	while 1:
		# do upgrade according schedule
		if rightTime("upg"):
			doUpdate()
		# do update variables according schedule
		if rightTime("var"):
			updateAllTimes()
			saveBridge()
			getPublicIP()
			if is_private(stp.myip):
				logstr = "Local"
			else:
				logstr = "Public"
			var.logger.debug(logstr + " IP address: " + stp.myip)
			update_ignores_2sit()
		# check max according schedule
		if rightTime("max"):
			# beta features here
			if tryRead("beta", "no", False).upper() == "YES":
				doProfiles()
			# end of beta
			cmd = getCMD()
			if cmd == "init":
				closeMAX()
				prepare()
			elif cmd == "mail":
				sendStatus()
			elif cmd == "quit":
				break
			elif cmd == "log_debug":
				var.logger.info("Logging level set to DEBUG")
				var.logger.setLevel(logging.DEBUG)
			elif cmd == "log_info":
				var.logger.info("Logging level set to INFO")
				var.logger.setLevel(logging.INFO)
			elif cmd[0:4] == "mute":
				key = cmd[4:]
				if key in var.d_W:
					var.d_W[key][0] = datetime.datetime.now()
					var.d_W[key][1] = True
					var.logger.debug("OWW for key " + str(key) + " is muted for " +
						str(stp.intervals["oww"][2]) + " seconds.")
			elif cmd == "rebridge":
				loadBridge()
			elif cmd == "updatetime":
				updateAllTimes()
			elif cmd == "led":
				if var.heating:
					queueMsg("H")
				else:
					queueMsg("S")
			elif cmd == "upgrade":
				doUpdate()
			readMAXData(False)
			if not var.error:
				getControlValues()
				doControl()
				doDevLogging()

		time.sleep(stp.intervals["slp"][0])


def getControlValues():
	# try read preference settings, total or per
	stp.preference = tryRead("pref", "per", True)
	# try read % valve for heat command
	stp.valve_switch = tryRead("valve", 35, True)
	stp.svpnmw = tryRead("svpnmw", 80, True)
	stp.total_switch = tryRead("total", 150, True)
	# setup total variable as integer
	stp.total = 100
	# try get readMAX interval value, if not set it
	stp.intervals["max"][0] = tryRead("int", 90, True)
	stp.intervals["slp"][0] = stp.intervals["max"][0] / stp.intervals["slp"][1]
	# try read num of valves to turn heat on
	stp.valve_num = tryRead("valves", 1, True)
	# try read if autoupdate is OK
	stp.au = tryRead("au", True, True)
	# try read how many minutes you can ignore valve after closing window
	var.ignore_time = tryRead("ign_op", 30, True)
	# and if open windows warning is disabled, 0 = enables, 1 = disabled
	var.no_oww = tryRead("no_oww", 0, True)


def prepare():
	stp.initIntervals()
	stp.initPaths()
	startLog()

	updateStatus("start")
	# initialize variables
	getControlValues()

	# initialize bridge values
	loadBridge()
	queueMsg("S")

	exportCSV("init")
	readMAXData(True)
	updateCounters(False)

if __name__ == '__main__':
	# values for setup system
	stp = setup()
	# variables
	var = variables()

	if os.path.ismount("/mnt/sda1"):
		stp.place = "/mnt/sda1/"
	elif os.path.ismount("/mnt/sdb1"):
		stp.place = "/mnt/sdb1/"
	else:
		err_str = "Error: can't find mounted storage device! Please mount SD card or USB key and run program again."
		llError(err_str)
		var.value.put(rCW("msg"), "Q")
		exit()

	result = getPublicIP()
	if result == 255:
		err_str = "Error getting IP address from hostname, please check resolv.conf or hosts or both!\r\n"
		llError(err_str)
		var.value.put(rCW("msg"), "Q")
		exit()

	execfile("/root/config.py")

	# after all, if myip is private address, web server port must be on 80 (by default)
	if result == 0 and is_private(stp.myip):
		stp.extport = 80
		var.localAddr = True

	# redir stderr to file
	redirErr(True)

	prepare()
	sendErrorLog()

	# check if exists directory for secondary we, if no, create
	try:
		os.makedirs(stp.place + "www")
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

	# this is it
	doLoop()

	# end show
	var.logger.close()
	updateStatus("dead")
	closeMAX()
	exportCSV("close")
	queueMsg("D")
	redirErr(False)
