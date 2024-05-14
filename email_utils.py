from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections.abc import Iterable
import smtplib


def send_mail(sender, recipients, subject, body):
    itr_recipients = recipients if isinstance(recipients, Iterable) else [recipients]
    msg_root = MIMEMultipart('related')
    msg_root['Subject'] = subject
    msg_root['From'] = sender
    msg_root['To'] = ','.join(itr_recipients)
    mail = MIMEMultipart('alternative')
    msg_root.attach(mail)
    mail.attach(MIMEText(body))

    mailserver = smtplib.SMTP()
    mailserver.connect('<hub>')
    mailserver.sendmail(sender, itr_recipients, msg_root.as_string())
    mailserver.close()
