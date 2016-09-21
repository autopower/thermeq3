import smtplib
import logmsg
import os
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64


def compose(m_id, m_body):
    """
    Compose message
    :param m_id: dictionary
    :param m_body: string
    :return: MIMEMultipart
    """
    c_msg = MIMEMultipart()
    c_msg["From"] = '"' + m_id["d"] + '" <' + m_id["f"] + ">"
    c_msg["To"] = ', '.join(m_id["t"])
    c_msg["Subject"] = m_id["s"]
    body = """<html><body><font face="arial,sans-serif">""" + m_body + "</p></body></html>"
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


def send_error_log(m_id, stderr_log, devname):
    """
    Send error log if any
    :param m_id: list
    :param stderr_log: string
    :param devname: string
    :return: -1 if no error log
    """
    if os.path.isfile(stderr_log) and os.path.getsize(stderr_log) > 0:
        body = ("<h1>%(a0)s status email.</h1>\n"
                "<p>Hello, I'm your thermostat and I sending you this email with error logfile as attachment.<br/>") \
               % {"a0": str(devname)}
        m_id.update({"s": m_id["d"] + " log email (thermeq3 device)"})
        msg = compose(m_id, body)
        msg.attach(attach_file(stderr_log))
        return send_email(m_id, msg.as_string())
    else:
        logmsg.update("Logfile: " + stderr_log)
        logmsg.update("Zero sized stderr log file, nothing'll be send")
        return False


def send_email(m_id, message):
    """
    sends email
    :param m_id: dictionary
    :param message:
    :return: boolean, true if success
    """
    m_server = m_id["sr"]
    m_port = m_id["p"]
    m_from_addr = m_id["f"]
    m_from_pwd = m_id["pw"]
    m_to_addr = m_id["t"]
    try:
        server = smtplib.SMTP(m_server, m_port)
    except Exception, error:
        logmsg.update(
            "Error connecting to mail server " + str(m_server) + ":" + str(m_port) + ". Error code: " + str(error))
        logmsg.update("Traceback: " + str(traceback.format_exc()))
    else:
        try:
            server.ehlo()
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()
            server.login(m_from_addr, m_from_pwd)
            server.sendmail(m_from_addr, m_to_addr, message)
        except smtplib.SMTPAuthenticationError:
            logmsg.update("Authentication error during sending email.")
        except Exception, error:
            logmsg.update("Error during sending email. Error code: " + str(error))
        else:
            server.quit()
            logmsg.update("Mail was sent.")
            return True
    return False
