import smtplib
import logmsg
import os
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
                
def compose(eq3Setup, subject, body):
    """
    Compose message
    :param eq3Setup: thermeq3.setup
    :param subject: string
    :param body: string
    :return: MIMEMultipart
    """
    c_msg = MIMEMultipart()
    c_msg["From"] = '"' + eq3Setup.devname + '" <' + eq3Setup.fromaddr + ">"
    c_msg["To"] = eq3Setup.toaddr if isinstance(eq3Setup.toaddr, basestring) else ','.join(eq3Setup.toaddr)
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


def send_error_log(eq3Setup, stderr_log):
    """
    Send error log if any
    :param eq3Setup: thermeq3.setup
    :param stderr_log: string
    :param devname: string
    :return: -1 if no error log
    """
    if os.path.isfile(stderr_log) and os.path.getsize(stderr_log) > 0:
        subject = eq3Setup.devname + " log email (thermeq3 device)"
        body = ("<h1>%(a0)s status email.</h1>\n"
                "<p>Hello, I'm your thermostat. I found this error log. It's attached.<br/>") \
               % {"a0": str(eq3Setup.devname)}
        msg = compose(eq3Setup, subject, body)
        msg.attach(attach_file(stderr_log))
        return send_email(eq3Setup, msg.as_string())
    else:
        logmsg.update("Logfile: " + stderr_log)
        logmsg.update("Zero sized stderr log file, nothing'll be send")
        return False


def send_email(eq3Setup, message):
    """
    sends email
    :param eq3Setup: thermeq3.setup
    :param message:
    :return: boolean, true if success
    """
    try:
        server = smtplib.SMTP(eq3Setup.mailserver, eq3Setup.mailport)
    except Exception, error:
        logmsg.update(
            "Error connecting to mail server " + str(eq3Setup.mailserver) + ":" + str(eq3Setup.mailport) + ". Error code: " + str(error))
        logmsg.update("Traceback: " + str(traceback.format_exc()))
    else:
        try:
            server.ehlo()
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()
            server.login(eq3Setup.mailuser, eq3Setup.mailpassword)
            server.sendmail(eq3Setup.fromaddr, eq3Setup.toaddr, message)
        except smtplib.SMTPAuthenticationError:
            logmsg.update("Authentication error during sending email.")
        except Exception, error:
            logmsg.update("Error during sending email. Error code: " + str(error))
        else:
            server.quit()
            logmsg.update("Mail was sent.")
            return True
    return False
