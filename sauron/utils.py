import smtplib
import os

from fabric.api import env

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from subprocess import Popen, PIPE

def get_mail_server():
    """ Return SMTP according to sauron.yml
    """
    mail_server = 'localhost'    
    if 'mail_server' in env.sauron['administrator']:
        mail_server = env_sauron['administrator']['mail_server']
    return mail_server

def send_mail(send_from, send_to, subject, text, files=[], html=False):
    """ Send an email

        send_from -- sender email
        send_to -- recipient
        subject -- mail subject
        text -- mail body (HTML ready)
        files -- a list of files URI to attach
        html -- true is body contains HTML false otherwise
        server -- smtp host
    """
    assert type(send_to) == list
    assert type(files) == list

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    part1 = ''
    if html:
        text += "<br>" + get_mail_signature(True)
        part1 = MIMEText(text, 'html', "utf-8")
    else:
        text += "\n" + get_mail_signature()
        part1 = MIMEText(text, 'plain', "utf-8")
    
    msg.attach(part1)

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)
    
    server = get_mail_server()
    if server.endswith('/sendmail'):
        # Use sendmail instead of an SMTP server
        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_string())
    else:
        smtp = smtplib.SMTP(server)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()

def get_mail_signature(html=False):
    """ Return mail signature according to given format

        html -- return html signature or text plain version
    """
    signature = ""
    if 'mail_signature' in env.sauron['administrator']:
        if html and 'html' in env.sauron['administrator']['mail_signature']:
            signature = env.sauron['administrator']['mail_signature']['html']
        elif not html and 'text' in env.sauron['administrator']['mail_signature']:
            signature = env.sauron['administrator']['mail_signature']['text']
    return signature
