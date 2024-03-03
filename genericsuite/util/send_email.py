# send_email.py
# 2023-06-18 | CR

# https://realpython.com/python-send-email/

from os import environ
from os.path import basename
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate

from genericsuite.util.app_logger import log_debug, log_error

DEBUG = False


def send_email(sender_email, receiver_email, subject, text,
               html, files=None):
    """
    Send an Email
    """
    files = [] if not files else files
    smtp_server = environ.get('SMTP_SERVER')
    smtp_port = environ.get('SMTP_PORT')  # For starttls
    smtp_user = environ.get('SMTP_USER')
    smtp_password = environ.get('SMTP_PASSWORD')
    if sender_email is None or sender_email.strip() == '':
        sender_email = environ.get('SMTP_DEFAULT_SENDER')

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message['To'] = COMMASPACE.join(receiver_email)
    message['Date'] = formatdate(localtime=True)

    # Turn these into plain/html MIMEText objects
    body_plain_text = MIMEText(text, "plain")
    if html:
        body_html = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(body_plain_text)
    if html:
        message.attach(body_html)

    for file_hdl in files or []:
        with open(file_hdl, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(file_hdl)
            )
        # After the file is closed
        # part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        part['Content-Disposition'] = 'attachment; filename=' + \
                                      f'"{basename(file_hdl)}"'
        message.attach(part)

    if DEBUG:
        log_debug('SEND_EMAIL' +
                   f'\n | smtp_server: {smtp_server}' +
                   f'\n | smtp_port: {smtp_port}' +
                   f'\n | smtp_user: {smtp_user}' +
                   f'\n | smtp_password: {"*" * len(smtp_password)}' +
                   f'\n | sender_email: {sender_email}' +
                   f'\n | receiver_email: {receiver_email}' +
                   f'\n | subject: {subject}' +
                   f'\n | text: {text}' +
                   f'\n | html: {html}' +
                   f'\n | file_path: {files}')

    # Create a secure SSL context
    context = ssl.create_default_context()
    # Try to log in to smtp server and send email
    try:
        smtp = smtplib.SMTP(smtp_server, smtp_port)
        # smtp.ehlo()  # Can be omitted
        smtp.starttls(context=context)  # Secure the connection
        # smtp.ehlo()  # Can be omitted
        smtp.login(smtp_user, smtp_password)
    except Exception as err:
        # Print any error messages to stdout
        log_error(f'Send_Email ERROR (preparing phase): {err}')
        return False
    try:
        smtp.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as err:
        # Print any error messages to stdout
        log_error(f'Send_Email ERROR (sending phase): {err}')
    finally:
        smtp.close()
    return True
