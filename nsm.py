#!/usr/bin/env python
import socket
import base64
import sys
import time
sys.path.insert(0, "/usr/lib/python2.7/bridge/") 
from bridgeclient import BridgeClient
from datetime import timedelta, datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import Encoders
from os import getpid, path, rename
import smtplib
import logging
import traceback
import urllib2
import hashlib
import httplib

class setup: pass
class variables: pass

#
# error handling, primitive but funny
#
##def myHandler(type, value, tb):
##	var.logger.exception("Uncaught exception: {0}".format(str(value)))
	
def redirErr(onoff):
	if onoff:
		var.ferr = open(stp.stderr_log, "a")
		var.original_stderr = sys.stderr
		sys.stderr = var.ferr
		print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection active"
	else:
		print >> sys.stderr, time.strftime("%H:%M:%S", time.localtime()), "Redirection closed"
		sys.stderr = var.original_stderr
		var.ferr.close()

def llError(err_string):
	err_file = open("/root/nsm.error", "a")
	err_file.write(time.strftime("%H:%M:%S", time.localtime()) + "\t" + err_string + "\r\n")
	err_file.close()
	
#
# helpers
#
def hexify(tmpadr):
	return "".join("%02x" % ord(c) for c in tmpadr)

def getHash(filename):
	checksum = hashlib.md5()
	if path.isfile(filename):
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
		return str(timedelta(seconds = uptime_seconds)).split(".")[0]

def incErr():
	tmp = tryRead("errs", 0, False)
	var.value.put(stp.cw["errs"], str(tmp+1))

def sendMSG():
	payload = var.msgQ[0:1]
	var.logger.debug("sending message [" + str(payload) + "]")
	if payload == "E":
		var.error = True
		var.err2Clear = True
	elif payload == "C":
		var.err2Clear = False
		var.err2LastStatus = True
		var.logger.info("Clearing error LED")
	elif payload == "R":
		saveBridge()
	var.value.put(stp.cw["msg"], str(payload))
	var.msgQ = var.msgQ[1:]

def qMSG(payload):
	var.logger.debug("Queqing [" + payload + "]")
	var.msgQ += payload
	while len(var.msgQ) > 0:
		var.logger.debug("Queue [" + str(var.msgQ) + "]")
		tmpvar = str(var.value.get(stp.cw["msg"]))
		if tmpvar == "":
			sendMSG()
		time.sleep(stp.timeout)

def getCMD():
	localcmd = var.value.get(stp.cw["cmd"])
	if localcmd is None:
		return ""
	elif len(localcmd) > 0:
		var.value.put(stp.cw["cmd"], "")
		var.logger.info("received command: [" + localcmd + "]")
	return localcmd

def isTime():
	this_now = time.time()
	t_h = this_now.tm_hour
	t_m = this_now.tm_min
	for k in range(len(stp.int)):
		nf = time.strptime(stp.int[k][0], "%H:%M")
		hf = nf.tm_hour
		mf = nf.tm_min
		nt = time.strptime(stp.int[k][1], "%H:%M")
		ht = nt.tm_hour
		mt = nt.tm_min
		if t_h >= hf and t_m >= mf and t_h < ht and t_m < mt:
			return k
	return -1

def tryRead(cw, default, save):
	if type(default) is str:
		isNum = False
	else:
		isNum = True
	lcw = stp.cw[cw]

	tmp_str = var.value.get(str(lcw))

	if tmp_str == "None":
		tmp = default
	else:
		if isNum:
			try:
				tmp = int(tmp_str)
			except:
				tmp = default
		else:
			tmp = tmp_str
	if save:
		var.value.put(str(lcw), str(tmp))
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

def updateUptime(tmp):
	var.value.put(stp.cw["uptime"], str(getUptime()))
	var.value.put(stp.cw["appuptime"], str(timedelta(seconds = int(tmp - stp.appStartTime))))
	var.t_nextUpdate = tmp + stp.i_update

def updateAllTimes(tmp):
	updateUptime(tmp)
	if var.heating:
		updateHeat(False)	

def updateStatus(statusMsg):
	var.value.put(stp.cw["status"], str(statusMsg))
	
def sendEmail(sendTxt):
	try:
		server = smtplib.SMTP(stp.mailserver, stp.mailport)
	except Exception, error:
		var.logger.error("Error connecting to mail server " +  str(stp.mailserver) + ":" + str(stp.mailport) + ". Error code: " + str(error))
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
	f = open(stp.bridgefile, "w")
	for k, v in stp.cw.iteritems():
		try:
			tmp = var.value.get(v)
		except:
			tmp = ""
		if tmp == "None" or tmp is None:
			tmp = ""
		f.write(v + "=" + tmp + "\r\n")
	f.close()
	
def loadBridge():
	if path.exists(stp.bridgefile):
		with open(stp.bridgefile, "r") as f:
			for line in f:
				if not stp.cw["dump"] in line:
					t = (line.rstrip("\r\n")).split('=')
					if t[0] in stp.cw.viewvalues():
						var.value.put(t[0], t[1])
					else:
						var.logger.critical("Error processing bridge file. Codeword: [" + str(t[0]) + "] with value [" + str(t[1]) +"]")
			f.close()
		updateAllTimes(time.time())
		return True
	else:
		return False


#
# autoupdate routines
#
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
					var.logger.error("Problems downloading new version. Result=" + str(down_result) + ", file=" + str(t[1]))
			else:
				return 1

	if not errstr == "":
		var.logger.error(errstr)
	return 0

def doUpdate():
	var.logger.debug("doUpdate() START")
	chk = checkUpdate()
	if chk == 2:
		rename(stp.homedir + "nsm.upd", stp.homedir + "nsm.py")
		temp_key = stp.maxid["sn"]
		body = """<html><body><font face="arial,sans-serif">
		<h1>Device upgrade information.</h1>
		<p>Hello, I'm your thermostat and I have a information for you.<br/>
		Please take a note, that I found new version of my control script and I'll be upgraded in few seconds.</br>
		Resistance is futile :).<br/>
		</p></body></html>"""
		sendWarning("upgrade", temp_key, body)
		qMSG("R")
	var.logger.debug("doUpdate() STOP")
		                
#
# send this, send that
#
def sendErrorLog():
	var.logger.debug("sendErrorLog() START")
	if path.getsize(stp.stderr_log) > 0:
		devname = stp.devname
		msg = MIMEMultipart()
		msg["From"] = stp.fromaddr
		#msg['To'] = stp.toaddr
		msg["To"] = ''.join(stp.toaddr)
		msg["Subject"] = devname + " log email (thermeq3 device)"

		body = """<html><body><font face="arial,sans-serif">
		<h1>%(a0)s status email.</h1>
		<p>Hello, I'm your thermostat and I sending you this email with error logfile as attachment.<br/>
		</p></body></html>""" % \
		{"a0": str(devname)}
		msg.attach(MIMEText(body, "html"))
	
		part = MIMEBase("application", "octet-stream")
		part.set_payload(open(stp.stderr_log, "rb").read())
		Encoders.encode_base64(part)
		head, tail = path.split(stp.stderr_log)
		part.add_header("Content-Disposition", "attachment; filename=\"" + tail + "\"\"")
		msg.attach(part)

		if sendEmail(msg.as_string()) == 0:
			var.value.put(stp.cw["errs"], "0")
			var.ferr.close()
			var.ferr = open(stp.stderr_log, "w")
	else:
		var.logger.info("Zero sized stderr log file, nothing'll be send")
	var.logger.debug("sendErrorLog() STOP")
	
def sendStatus():
	var.logger.debug("sendStatus() START")
	devname = stp.devname
	valve_pos = int(var.value.get(stp.cw["valve"]))
	error = int(var.value.get(stp.cw["errs"]))
	status = var.value.get(stp.cw["status"])
	interval = int(var.value.get(stp.cw["int"]))
	totalerrs = int(var.value.get(stp.cw["terrs"]))

	uptime_string = getUptime()

	var.value.put(stp.cw["terrs"], str(totalerrs + error))
	msg = MIMEMultipart()
	msg["From"] = stp.fromaddr
	#msg['To'] = stp.toaddr
	msg["To"] = ''.join(stp.toaddr)
	msg["Subject"] = devname + " status email (thermeq3 device)"

	heat_str = var.value.get(stp.cw["htstr"])
	
	body = """<html><body><font face="arial,sans-serif">
	<h1>%(a0)s status email.</h1>
	<p>Hello, I'm your thermostat and I sending you this status email.<br/>
	Actual system status <b>%(a1)s</b> is checked every <b>%(a5)02d</b> seconds
	for valve position of <b>%(a6)02d%%</b>.<br/>
	Total heating time is <b>%(a3)s</b><br/>
	Errors from last status mail: <b>%(a2)s</b><br/>
	Total errors since start: <b>%(a7)d</b><br/>
	Device uptime: <b>%(a8)s</b><br/>
	Application uptime: <b>%(a9)s</b><br/>
	</p></body></html>""" % \
	{'a0': str(devname), \
	 'a1': status, \
	 'a2': str(error), \
	 'a3': heat_str, \
	 'a5': interval, \
	 'a6': valve_pos, \
	 'a7': totalerrs, \
	 'a8': uptime_string, \
	 'a9': str(timedelta(seconds = int(time.time() - stp.appStartTime))) \
	}

	msg.attach(MIMEText(body, "html"))

	if sendEmail(msg.as_string()) == 0:
		var.value.put(stp.cw["errs"], "0")
	var.logger.debug("sendStatus() STOP")

def silence(key, isWin):
	# is there key in dict?
	dt = datetime.now()
	if not var.d_W.has_key(key):
		var.logger.debug("No key " + str(key) + " in d_W. Key added.")
		if isWin:
			var.d_W.update({key:[stp.devices[key][5], False, 0]})
		else:
			var.d_W.update({key:[dt, False, 0]})
		return 2
	else:
		# yes, there it is, so check if we are silent, if so exit, otherwise reset mute
		if var.d_W[key][1]:
			if isWin:
				tmp = var.d_W[key][0] + timedelta(seconds = stp.mute_OW)
			else:
				tmp = var.d_W[key][0] + timedelta(seconds = stp.mute_W)
			if tmp < dt:
				return 1
			else:
				var.d_W[key][1] = False
	var.d_W[key][2] += 1
	if var.d_W[key][2] > stp.abnormalCount:
		var.logger.critical("Abnormal count of warnings for device [" + str(key) + "], name [" + str(stp.devices[key][2]) + "]")
		stp.abnormalCount = 0
	return 0
	
def sendWarning(selector, dev_key, body_txt):
	var.logger.debug("sendWarning(" + str(selector) + ") START")
	tm = time.time()
	devname = stp.devname
	if selector != "openmax" or selector != "upgrade":
		d = stp.devices[dev_key]
		dn = d[2]
		r = d[3]
		rn = stp.rooms[str(r)]
	sil = silence(dev_key, selector == "window")
	if sil == 1:
		var.logger.debug("Warning for device " + str(dev_key) + " is muted!")
		return

	mutestr = "http://" + stp.myip + "/data/put/command/mute" + str(dev_key)
	msg = MIMEMultipart()
	msg["From"] = stp.fromaddr
	msg["To"] = stp.toaddr
	
	if selector == "window":
		owd = int((datetime.now() - stp.devices[dev_key][5]).total_seconds())
		oww = int((datetime.now() - var.d_W[dev_key][0]).total_seconds())
		if sil == 0 and oww < stp.i_OW:
			var.logger.debug("sendWarning() STOP, condition not met. Trace=" + str(oww) + "/" + str(var.d_W[dev_key][0]))
			return
		msg["Subject"] = "Open window in room " + str(rn[0]) + ". Warning from " + devname + " (thermeq3 device)"
		body = """<html><body><font face="arial,sans-serif">
		<h1>Device %(a0)s warning.</h1>
		<p>Hello, I'm your thermostat and I have a warning for you.<br/>
		Please take a care of window <b>%(a0)s</b> in room <b>%(a1)s</b>.
		Window in this room is now opened more than <b>%(a2)d</b> mins.<br/>
		Threshold for warning is <b>%(a3)d</b> mins.<br/>
		</p><p>You can <a href="%(a4)s">mute this warning</a> for %(a5)s mins. \
		</p></body></html>""" % \
		{'a0': str(dn), \
		 'a1': str(rn[0]), \
		 'a2': int(owd / 60), \
		 'a3': int(stp.w_OW / 60), \
		 'a4': str(mutestr), \
		 'a5': int(stp.mute_OW / 60)}
	else:
		if sil == 0 and tm < var.t_nextWarn:
			var.logger.debug("sendWarning() stop")
			return
		var.t_nextWarn = tm + stp.i_nextWarn
		if selector == "battery":
			msg["Subject"] = "Battery status for device " + str(dn) + ". Warning from " + devname + " (thermeq3 device)"
			body = """<html><body><font face="arial,sans-serif">
			<h1>Device %(a0)s battery status warning.</h1>
			<p>Hello, I'm your thermostat and I have a warning for you.<br/>
			Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
			This device have low battery, please replace batteries.<br/>
			</p><p>You can <a href="%(a2)s">mute this warning</a> for %(a2)s mins. \
			</p></body></html>""" % \
			{'a0': str(dn), \
		 	'a1': str(rn[0]), \
		 	'a2': int(stp.mute_W / 60)}
		elif selector == "error":
			msg["Subject"] = "Error report for device " + str(dn) + ". Warning from " + devname + " (thermeq3 device)"
			body = """<html><body><font face="arial,sans-serif">
			<h1>Device %(a0)s radio error.</h1>
			<p>Hello, I'm your thermostat and I have a warning for you.<br/>
			Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
			This device reports error.<br/>
			</p><p>You can <a href="%(a2)s">mute this warning</a> for %(a2)s mins. \
			</p></body></html>""" % \
			{'a0': str(dn), \
		 	'a1': str(rn[0]), \
		 	'a2': int(stp.mute_W / 60)}
		elif selector == "openmax":
			msg["Subject"] = "Can't connect to MAX! Cube! Warning from " + devname + " (thermeq3 device)"
			body = body_txt
		elif selector == "upgrade":
			msg["Subject"] = devname + " (thermeq3 device) is going to be upgraded"
			body = body_txt
	
	msg.attach(MIMEText(body, "html"))
	if sendEmail(msg.as_string()) == 0 and selector == "window":
		var.d_W[dev_key][0] = datetime.now()
	var.logger.debug("sendWarning() STOP")
	
#
# logging etc
#
def startLog():
	var.logger = logging.getLogger("thermeq3")
	var.logger.setLevel(logging.DEBUG)

	#var.fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*(1024*1024), backupCount=10)

	var.fh = logging.FileHandler(stp.log_filename)
	var.fh.setLevel(logging.DEBUG)
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%d/%m/%Y %H:%M:%S")
	var.fh.setFormatter(formatter)
	var.logger.addHandler(var.fh)

	var.logger.info("app V" + str(stp.version) + " started with PID=" + str(getpid()) + " and created logfile")
	#logger.debug('debug message')
	#logger.warn('warn message')
	#logger.critical('critical message')

def exportCSV(onoff):
	if onoff == "init":
		if path.exists(stp.csv_log):
			rename(stp.csv_log, stp.place + stp.devname + "_" + time.strftime("%d%m%Y-%H%M%S", time.localtime()) + ".csv")
		var.csv = open(stp.csv_log, "a")
	elif onoff == "headers":
		for k, v in stp.valves.iteritems():
			var.csv.write(stp.devices[k][2] + "," + stp.devices[k][2] + ",")
		var.csv.write("\r\n")
	elif onoff == "close":
		var.csv.close()
		
#
# EQ-3/ELV MAX! communication
#
def openMAX():
	var.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	var.client_socket.settimeout(int(stp.timeout / 2))	
	temp_key = stp.maxid["sn"]

	try:
		var.client_socket.connect((stp.max_ip, 62910))
	except Exception, e:
		incErr()
		var.logger.error("Error opening connection to MAX Cube. Error: " + str(e))
		var.logger.error("Traceback: " + str(traceback.format_exc()))
		body = """<html><body><font face="arial,sans-serif">
		<h1>Device %(a0)s warning.</h1>
		<p>Hello, I'm your thermostat and I have a warning for you.<br/>
		Please take a care of connection to MAX! Cube.</br>
		I can't connect to Cube at address <b>%(a1)s</b>.<br/>
		Error: %(a2)s<br/>
		Traceback: %(a3)s<br/>
		</p></body></html>""" % \
		{'a0': str(stp.devname), \
		 'a1': str(stp.max_ip), \
		 'a2': str(e), \
		 'a3': str(traceback.format_exc()) } 
		sendWarning("openmax", temp_key, body)
		return False
	else:
		if var.d_W.has_key(temp_key):
			var.logger.debug("Key " + str(temp_key) + " in d_W deleted.")
			del var.d_W[temp_key]
		return True

def readMAX(refresh):
	var.client_socket.settimeout(int(stp.timeout / 3))
	var.error = False
	this_now = datetime.now()
	for line in readlines(var.client_socket):
		data = line
		sd = data[2:].split(",")
		
		if data[0] == 'H':
			stp.maxid["sn"] = sd[0]
			stp.maxid["rf"] = sd[1]
			stp.maxid["fw"] = sd[2]
		elif data[0] == 'M':
			es = base64.b64decode(sd[2])
			room_num = ord(es[2])
			es_pos = 3
			for i in range(0, room_num):
				room_id = str(ord(es[es_pos]))
				room_len = ord(es[es_pos+1])
				es_pos += 2
				room_name = es[es_pos:es_pos + room_len]
				es_pos += room_len
				room_adr = es[es_pos:es_pos+3]
				es_pos += 3
				if not stp.rooms.has_key(room_id) or refresh:
					stp.rooms.update({room_id:[room_name, hexify(room_adr), False]})

			dev_num = ord(es[es_pos])
			es_pos += 1
			for i in range(0, dev_num):
				dev_type = ord(es[es_pos])
				es_pos += 1
				dev_adr = hexify(es[es_pos:es_pos+3])
				es_pos += 3
				dev_sn = es[es_pos:es_pos+10]
				es_pos += 10
				dev_len = ord(es[es_pos])
				es_pos += 1
				dev_name = es[es_pos:es_pos+dev_len]
				es_pos += dev_len
				dev_room = ord(es[es_pos])
				es_pos += 1
				if not stp.devices.has_key(dev_adr) or refresh:
					#                            type      serial  name      room     OW, OW_time, status, info, temp offset
					stp.devices.update({dev_adr:[dev_type, dev_sn, dev_name, dev_room, 0, this_now, 0, 0, 7]})
		elif data[0] == 'C':
			es = base64.b64decode(sd[1])
			if ord(es[0x04]) == 1:
				dev_adr = hexify(es[0x01:0x04])
				stp.devices[dev_adr][8] = es[0x16]
		elif data[0] == 'L':
			es = base64.b64decode(sd[0])
			es_pos = 0
			while (es_pos < len(es)):
				dev_len = ord(es[es_pos]) + 1
				valve_adr = hexify(es[es_pos+1:es_pos+4])
				valve_status = ord(es[es_pos + 0x05])
				valve_info = ord(es[es_pos + 0x06])
				valve_temp = 0xFF
				if dev_len == 12:
					valve_pos = ord(es[es_pos + 0x07])
					if valve_info & 3 != 2:
						valve_temp = ord(es[es_pos + 0x0A])
					stp.valves.update({valve_adr:[valve_pos, valve_temp]})
				elif dev_len == 7:
					tmp_open = ord(es[es_pos + 0x06]) & 2
					if tmp_open != stp.devices[valve_adr][4]:
						tmp_txt = "Window contact " + str(stp.devices[valve_adr][2]) + " is now "
						if tmp_open == 0:
							var.logger.info(tmp_txt + "closed.")
							if var.d_W.has_key(valve_adr):
								var.logger.debug("Key " + str(valve_adr) + " in d_W deleted.")
								del var.d_W[valve_adr]
						else:
							var.logger.info(tmp_txt + "opened.")
						stp.devices[valve_adr][4] = tmp_open
						stp.devices[valve_adr][5] = datetime.now()
				stp.devices[valve_adr][6] = valve_status
				stp.devices[valve_adr][7] = valve_info
				es_pos += dev_len

def closeMAX():
	var.client_socket.close()

#
# some stupid commands :)
#
def updateHeat(regular):
	tmp = tryRead("ht", 0, False)
	diff = time.time() - var.heatStart
	totalheat = int(tmp + diff)
	var.value.put(stp.cw["ht"], str(totalheat))
	var.value.put(stp.cw["htstr"],  str(timedelta(seconds = totalheat)))
	var.logger.info("heat time counter updated to " + str(timedelta(seconds = totalheat)) + "(" + str(tmp) + "/" + str(diff) + ")")
	if not regular:
		var.heatStart = time.time()

def dumpMAX(method):
	var.logger.debug("dumpMAX() START")
	txt = "DEVICES="
	for k, v in stp.devices.iteritems():
		txt = txt + "[" + str(k).upper() + "]/[" + str(v) + "]; "
	txt = txt + "\r\nVALVES="
	for k, v in stp.valves.iteritems():
		txt = txt + "[" + str(k).upper() + "]/[" + str(v) + "]; "
	if method == 1:
		var.logger.debug(txt)
	else:
		var.value.put(stp.cw["dump"], txt)
	var.logger.info("dumpMAX() system dumped")
	var.logger.debug("dumpMAX() STOP")

def readMAXData(refresh):
	var.logger.debug("readData() START")
	if not openMAX():
		qMSG("E")
	else:
		readMAX(refresh)
		logstr = "Valve switch ratio is " + str(stp.valve_switch) + ", actual valves positions are:"
		tmpstr = "Valve temperatures are:"
		var.csv.write(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime()) + ",")
		for k, v in stp.valves.iteritems():
			logstr += "\r\n(" + str(stp.devices[k][2]) + "/" + str(k) + ")=(" + str(v[0]) + "%)"
			var.csv.write(str(v[0]) + "," + str(float(v[1]) / 10) + ",")
			tmpstr += "\r\n(" + str(stp.devices[k][2]) + "/" + str(float(v[1] / 10)) + ")"
		var.csv.write("\r\n")
		var.logger.debug(logstr)
		var.logger.debug(tmpstr)
	closeMAX()
	var.logger.debug("readData() STOP")
	
#
# and here we go, this is app logic
#
def doControl():
	heat = False
	if stp.preference == "total":
		stp.total = stp.total_switch
	elif stp.preference == "per":
		stp.total = stp.per_switch * len(stp.valves)
	for k, v in stp.devices.iteritems():
		if v[0] == 4 and v[4] == 2: # so its windows shutter contact and is open
			tmp = (datetime.now() - v[5]).total_seconds()
			if tmp > stp.w_OW:
				var.logger.debug("Warning condition for window " + str(k) + " met")
				sendWarning("window", k, "")
		if v[7] & 128 == 128: # theres a battery error
			sendWarning("battery", k, "")
		if v[6] & 8 == 8: # radio error
			sendWarning("error", k, "")
	grt = 0 # grand total of valve positions
	for k, v in stp.valves.iteritems():
		if v[0] > stp.valve_switch:
			heat = True
		grt += v[0]
	if not heat and grt >= stp.total:
			heat = True
	if var.err2Clear and not var.error:
		qMSG("C")
	if var.err2LastStatus:
		var.err2LastStatus = False
		if var.heating:
			qMSG("H")
			var.logger.info("Resuming heating state on status LED")
	if heat != var.heating:
		if heat:
			var.heating = True
			qMSG("H")
			txt = "heating started due to "
			if grt >= stp.total:
				txt += "sum of valve positions = " + str(grt) 
			else:
				d = stp.devices[k]
				dn = d[2]
				r = d[3]
				rn = stp.rooms[str(r)]
				txt += "room " + str(rn[0]) + ", device " + str(dn) + " with value " + str(v)
			var.logger.info(txt)
			var.heatStart = time.time()
			updateStatus(stp.statMsg["heat"])
		else:
			var.heating = False
			qMSG("S")
			updateStatus(stp.statMsg["idle"])
			updateHeat(True)
	
def doLoop():
	while 1:
		tmp_tm = time.time()
		if tmp_tm > var.t_nextUpdate:
			updateAllTimes(tmp_tm)
			saveBridge()
			doUpdate()
		if tmp_tm > var.t_nextLoop:
			cmd = getCMD()
			if cmd == "init":
				closeMAX()
				prepare()
			elif cmd == "mail":
				sendStatus()
			elif cmd == "quit":
				break
			elif cmd == "dump":
				dumpMAX(0)
			elif cmd == "log_debug":
				var.logger.info("Logging level set to DEBUG")
				var.logger.setLevel(logging.DEBUG)
			elif cmd == "log_info":
				var.logger.info("Logging level set to INFO")
				var.logger.setLevel(logging.INFO)
			elif cmd == "uptime":
				updateUptime(tmp_tm)
			elif cmd[0:4] == "mute":
				if var.d_W.has_key(cmd[4:]):
					var.d_W[cmd[4:]] = [datetime.now(), True]
					var.logger.debug("OWW with id[" + cmd[4:] + "] is now muted for " + str(stp.mute_OW) + " seconds.")
			elif cmd == "rebridge":
				loadBridge()
			elif cmd == "updatetime":
				updateAllTimes(tmp_tm)
			elif cmd == "led":
				if var.heating:
					qMSG("H")
				else:
					qMSG("S")
			elif cmd == "upgrade":
				doUpdate()
				
			readMAXData(False)
			if not var.error:
				getControlValues()
				doControl()

			var.t_nextLoop = tmp_tm + stp.i_nextLoop

		time.sleep(stp.i_nextLoop / 3)

	
def getControlValues():
	stp.preference = tryRead("pref", "total", True)
	stp.valve_switch = tryRead("valve", 33, True)
	if stp.preference == "per":
		stp.per_switch = tryRead("per", 10, True)
	elif stp.preference == "total":
		stp.total_switch = tryRead("total", 60, True)
	stp.total = 100
	# try get readMAX interval value, if not set it
	stp.i_nextLoop = tryRead("int", 90, True)

def setupInit():
	# threshold in seconds, so 10 minutes are 10*60 seconds
	# open windows warning is send every X seconds
	stp.i_OW = 30*60
	# open windows warning is 1st time send after, so windows is open X seconds
	stp.w_OW = 10*60
	# interval for other warnings
	stp.i_nextWarn = 60*60
	# next update interval for global variables (uptime, heating, bridge = you can lost only X seconds of thermeq's life)
	stp.i_update = 10*60
	# open window can be muted for
	stp.mute_OW = 15*60
	# other warning can be muted for
	stp.mute_W = 60*60
	# abnormal count of warning is
	stp.abnormalCount = 30

def varInit():
	# save time
	tmptm = time.time()
	var.t_nextOW = tmptm 
	var.t_nextUpdate = tmptm 
	var.t_nextWarn = tmptm
	# when will be next loop executed?
	var.t_nextLoop = tmptm
	# open window dictionary
	var.d_W = {}
	
def prepare():
	stp.github = "https://raw.github.com/autopower/thermeq3/master/"
	stp.homedir = "/root/"
	stp.log_filename = stp.place + stp.devname + ".log"
	startLog()
	stp.appStartTime = time.time()
			
	stp.csv_log = stp.place + stp.devname + ".csv"
	stp.bridgefile = stp.place + stp.devname + ".bridge"
 
	# dictionaries for MAX
	stp.maxid = {"sn":"000000", "rf":"", "fw":""}
	stp.valves = {}
	stp.rooms = {}
	stp.devices = {}
	
	# initialize variables
	setupInit()
	varInit()
	getControlValues()
	
	var.heatStart = 0
	var.csv = None
	# clear errors
	var.heating = False
	var.err2Clear = False
	var.err2LastStatus = False
	var.error = False
	# initialize bridge values
	if not loadBridge():
		var.value.put(stp.cw["errs"], "0")
		var.value.put(stp.cw["terrs"], "0")
		var.value.put(stp.cw["ht"], "0")
		var.value.put(stp.cw["cmd"], "")
	updateStatus(stp.statMsg["start"])
	
	exportCSV("init")
	readMAXData(True)
	exportCSV("headers")
	
if __name__ == '__main__':
	stp = setup()
	stp.version = 104
	stp.cw = {"status":"status", \
		  "int":   "interval", \
		  "ht":    "heattime", \
		  "errs":  "error", \
		  "terrs": "totalerrors", \
		  "valve": "valve_pos", \
		  "cmd":   "command", \
		  "msg":   "msg", \
		  "dump":  "dumpdata", \
		  "uptime":"uptime", \
		  "appuptime":"app_uptime", \
		  "total": "total_switch", \
		  "per":   "per_switch", \
		  "pref":  "preference", \
		  "htstr": "heattime_string"}
	stp.statMsg = {"idle": "idle", "heat": "heating", "start": "starting", "dead": "dead"}
	var = variables()
	var.msgQ = ""
	
	# initialize bridge
	var.value = BridgeClient()
	
	if path.ismount("/mnt/sda1"):
		stp.place = "/mnt/sda1/"
	elif path.ismount("/mnt/sdb1"):
		stp.place = "/mnt/sdb1/"
	else:
		err_str = "Error: can't find mounted storage device! Please mount SD card or USB key and run program again."
		llError(err_str)
		var.value.put(stp.cw["msg"], "Q")
		exit()
	
	try:
		stp.myip = socket.gethostbyname(socket.gethostname())
	except Exception, e:
		err_str = "Error getting IP address from hostname, please check resolv.conf or hosts or both!\r\n"
		err_str += "Error code: " + str(e) + "\r\n"
		err_str += "Traceback: " + str(traceback.format_exc()) +"\r\n"
		llError(err_str)
		var.value.put(stp.cw["msg"], "Q")
		exit()
	
	execfile("/root/config.py")
		
	stp.stderr_log = stp.place + stp.devname + "_error.log"

	#redir stderr
	redirErr(True)
	
	#sys.excepthook = myHandler
	prepare()
	sendErrorLog()
	doUpdate()
	doLoop()
	var.logger.close()
	updateStatus(stp.statMsg["dead"])
	closeMAX()
	exportCSV("close")
	qMSG("D")
	redirErr(False)
