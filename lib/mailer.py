import smtplib
import logmsg
import os
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
import thermeq3

subject_body = {"battery": ["Battery status for device %(b0)s. Warning from thermeq3 device",
                            """<h1>Device %(a0)s battery status warning.</h1>
                            <p>Hello, I'm your thermostat and I have a warning for you.<br/>
                            Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
                            This device have low batteries, please replace batteries.<br/>
                            </p><p>You can <a href="%(b0)s">mute this warning</a> for %(a3)s mins."""],
                "error": ["Error report for device %(a0)s. Warning from thermeq3 device",
                          """<h1>Device %(a0)s radio error.</h1>
                          <p>Hello, I'm your thermostat and I have a warning for you.<br/>
                          Please take a care of device <b>%(a0)s</b> in room <b>%(a1)s</b>.
                          This device reports error.<br/>
                          </p><p>You can <a href="%(b0)s">mute this warning</a> for %(a3)s mins."""],
                "openmax": ["Can't connect to MAX! Cube! Warning from thermeq3 device", ""],
                "upgrade": ["thermeq3 device is going to be upgraded", ""],
                "window": ["Open window in room %(b0)s. Warning from thermeq3 device",
                           """<h1>Device %(a0)s warning.</h1>
                           <p>Hello, I'm your thermostat and I have a warning for you.<br/>
                           Please take a care of window <b>%(a0)s</b> in room <b>%(a1)s</b>.
                           Window in this room is now opened more than <b>%(a2)s</b>.<br/>
                           Threshold for warning is <b>%(a3)d</b> mins.<br/>
                           </p><p>You can <a href="%(a4)s">mute this warning</a> for %(a5)s mins."""]
                }


def new_compose(selector, b0, a0, a1="", a2="", a3=0, a4="", a5=0):
    global subject_body
    subject = subject_body[selector][0] % {'b0': str(b0)}
    if selector == "window":
        body = subject_body[selector][1] % {'a0': str(a0), 'a1': str(a1), 'a2': str(a2), 'a3': int(a3),
                                            'a4': str(a4), 'a5': int(a5)}
    elif selector == "openmax" or selector == "upgrade":
        body = a0
    else:
        body = subject_body[selector][1] % {'a0': str(a0), 'a1': str(a1), 'a2': str(a2), 'a3': int(a3)}

    c_msg = MIMEMultipart()
    t3_setup = thermeq3.t3.setup
    c_msg["From"] = '"' + t3_setup.device_name + '" <' + t3_setup.from_addr + ">"
    c_msg["To"] = t3_setup.to_addr if isinstance(t3_setup.to_addr, basestring) else ','.join(t3_setup.to_addr)
    c_msg["Subject"] = subject
    body = """<html><body><font face="arial,sans-serif">""" + body + "</p></body></html>"
    c_msg.attach(MIMEText(body, "html"))

    return c_msg


def expand_address_list(address_list):
    return address_list if isinstance(address_list, basestring) else ','.join(address_list)


def str_to_list(tmp_str):
    tmp = tmp_str.replace("[", "").replace("]", "")
    return tmp.split(",")


def compose(eq3_setup, subject, body):
    """
    Compose message
    :param eq3_setup: thermeq3.setup
    :param subject: string
    :param body: string
    :return: MIMEMultipart
    """
    c_msg = MIMEMultipart()
    c_msg["From"] = '"' + str(eq3_setup.device_name) + '" <' + str(eq3_setup.from_addr) + ">"
    c_msg["To"] = expand_address_list(eq3_setup.to_addr)
    c_msg["Subject"] = subject
    body = """<html><body><font face="arial,sans-serif">""" + body + "</p></body></html>"
    c_msg.attach(MIMEText(body, "html"))

    return c_msg


def attach_file(filename):
    """
    Attach filename
    :param filename: string
    :return: MIMEBase
    """
    part = MIMEBase("application", "octet-stream")
    part.set_payload(open(filename, "rb").read())
    encode_base64(part)
    basename = os.path.basename(filename)
    attachment_filename = os.path.splitext(basename)[0]
    # for better attachment handling and reading on mobile devices
    part.add_header("Content-Disposition", "attachment; filename=\"" + attachment_filename + ".txt\"\"")
    return part


def send_error_log(eq3_setup, stderr_log):
    """
    Send error log if any
    :param eq3_setup: thermeq3.setup
    :param stderr_log: string
    :return: -1 if no error log
    """
    if not (not os.path.isfile(stderr_log) or not (os.path.getsize(stderr_log) > 0)):
        subject = eq3_setup.device_name + " log email (thermeq3 device)"
        body = ("<h1>%(a0)s status email.</h1>\n"
                "<p>Hello, I'm your thermostat.<br/>"
                " I found this error log. It's attached.<br/>") % {"a0": str(eq3_setup.device_name)}
        msg = compose(eq3_setup, subject, body)
        msg.attach(attach_file(stderr_log))
        return send_email(eq3_setup, msg.as_string())
    else:
        logmsg.update("Logfile: " + stderr_log)
        logmsg.update("Zero sized stderr log file, nothing'll be send")
        return False


def send_email(eq3_setup, message):
    """
    sends email
    :param eq3_setup: thermeq3.setup
    :param message:
    :return: boolean, true if success
    """
    try:
        server = smtplib.SMTP(eq3_setup.mail_server, eq3_setup.mail_port)
    except Exception, error:
        logmsg.update(
            "Error connecting to mail server " + str(eq3_setup.mail_server) + ":" + str(
                eq3_setup.mail_port) + ". Error code: " + str(error))
        logmsg.update("Traceback: " + str(traceback.format_exc()))
    else:
        try:
            server.ehlo()
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()
            server.login(eq3_setup.from_addr, eq3_setup.from_pwd)
            tmp = str_to_list(eq3_setup.to_addr)
            server.sendmail(eq3_setup.from_addr, str_to_list(eq3_setup.to_addr), message)
        except smtplib.SMTPAuthenticationError:
            logmsg.update("Authentication error during sending email.")
        except smtplib.SMTPRecipientsRefused:
            logmsg.update("Recipient refused.")
        except Exception, error:
            logmsg.update("Error during sending email. Error code: " + str(error))
        else:
            server.quit()
            logmsg.update("Mail was sent.")
            return True
    return False
