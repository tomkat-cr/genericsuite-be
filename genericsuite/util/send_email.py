# send_email.py
# 2023-06-18 | CR

# https://realpython.com/python-send-email/

from typing import Optional, Union
from os import environ
from os.path import basename

import re
import ssl
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate, make_msgid

from genericsuite.util.utilities import get_default_resultset
from genericsuite.util.app_logger import log_debug, log_error

DEBUG = environ.get('SEND_EMAIL_DEBUG', '0') == '1'


def parse_recipients(*fields: Union[list[str], str, None]) -> list[str]:
    """Split comma-separated address strings into a flat list of addresses.

    smtplib.sendmail() does not split on commas: a string is treated as one
    envelope recipient. Pass a list of individual addresses instead.
    """
    addrs = []
    for field in fields:
        if not field:
            continue
        if isinstance(field, (list, tuple)):
            for item in field:
                addrs.extend(parse_recipients(item))
        else:
            addrs.extend(a.strip() for a in str(field).split(",") if a.strip())
    # Preserve order, drop duplicates
    seen = set()
    unique = []
    for addr in addrs:
        if addr not in seen:
            seen.add(addr)
            unique.append(addr)
    return unique


def remove_html_tags(text: str) -> str:
    """Remove html tags from a string using regex"""
    # Pattern to match anything between '<' and '>'
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def send_email(
    sender_email: Union[str, None],
    receiver_email: Union[list[str], str, None],
    subject: str,
    text: str,
    html: str,
    files: Optional[list[str]] = None
) -> dict:
    """
    Send an Email
    """
    result = get_default_resultset()

    files = [] if not files else files
    smtp_server = environ.get('SMTP_SERVER')
    smtp_port_raw = environ.get('SMTP_PORT')  # For starttls
    smtp_user = environ.get('SMTP_USER')
    smtp_password = environ.get('SMTP_PASSWORD')

    if not sender_email:
        sender_email = environ.get('SMTP_DEFAULT_SENDER')
    if not (sender_email or '').strip():
        result['error'] = True
        result['error_message'] = 'Sender email is required'
        return result
    sender_email = sender_email.strip()

    if not receiver_email:
        receiver_email = []
    if isinstance(receiver_email, str):
        receiver_email = [receiver_email]
    if not receiver_email:
        result['error'] = True
        result['error_message'] = 'Receiver email is required'
        return result

    to_addrs = parse_recipients(receiver_email[0])
    cc_addrs = parse_recipients(receiver_email[1:]) if len(
        receiver_email) > 1 else []
    # Envelope must include every address that should receive the message
    envelope_recipients = parse_recipients(to_addrs, cc_addrs)

    if not subject:
        result['error'] = True
        result['error_message'] = 'Subject is required'
        return result

    if not text and not html:
        result['error'] = True
        result['error_message'] = 'Text or HTML is required'
        return result

    if not html:
        html = text
    elif not text:
        text = remove_html_tags(html)

    missing_smtp = [
        name for name, value in (
            ('SMTP_SERVER', smtp_server),
            ('SMTP_PORT', smtp_port_raw),
            ('SMTP_USER', smtp_user),
            ('SMTP_PASSWORD', smtp_password),
        ) if not value
    ]
    if missing_smtp:
        result['error'] = True
        result['error_message'] = (
            'Missing SMTP configuration: ' + ', '.join(missing_smtp)
        )
        return result

    try:
        smtp_port = int(smtp_port_raw)
    except (TypeError, ValueError):
        result['error'] = True
        result['error_message'] = f'Invalid SMTP_PORT: {smtp_port_raw}'
        return result

    _ = DEBUG and log_debug(
        'SEND_EMAIL' +
        f'\n | sender_email: {sender_email}' +
        f'\n | to_addrs: {to_addrs}' +
        f'\n | cc_addrs: {cc_addrs}' +
        f'\n | subject: {subject}' +
        f'\n | text: {text}' +
        f'\n | html: {html}' +
        f'\n | files: {files}')

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message['To'] = COMMASPACE.join(to_addrs)
    if len(cc_addrs) > 0:
        message['Cc'] = COMMASPACE.join(cc_addrs)
    message['Date'] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid()

    # Turn these into plain/html MIMEText objects
    body_plain_text = MIMEText(text, "plain", "utf-8")
    if html:
        body_html = MIMEText(html, "html", "utf-8")

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
        part['Content-Disposition'] = 'attachment; filename=' + \
                                      f'"{basename(file_hdl)}"'
        message.attach(part)

    if DEBUG:
        password_mask = (
            '*' * len(smtp_password) if smtp_password else '(not set)'
        )
        log_debug(
            'SEND_EMAIL' +
            f'\n | smtp_server: {smtp_server}' +
            f'\n | smtp_port: {smtp_port}' +
            f'\n | smtp_user: {smtp_user}' +
            f'\n | smtp_password: {password_mask}' +
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
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            try:
                # smtp.ehlo()  # Can be omitted
                smtp.starttls(context=context)  # Secure the connection
                # smtp.ehlo()  # Can be omitted
                smtp.login(smtp_user, smtp_password)
            except Exception as err:  # pylint: disable=broad-except
                result['error'] = True
                result['error_message'] = (
                    f'Send_Email ERROR (preparing phase): {err}'
                )
                log_error(result['error_message'])
                return result

            try:
                smtp.sendmail(
                    sender_email,
                    envelope_recipients,
                    message.as_string(),
                )
            except Exception as err:  # pylint: disable=broad-except
                result['error'] = True
                result['error_message'] = (
                    f'Send_Email ERROR (sending phase): {err}'
                )
                log_error(result['error_message'])
                return result
    except Exception as err:  # pylint: disable=broad-except
        result['error'] = True
        result['error_message'] = f'Send_Email ERROR (preparing phase): {err}'
        log_error(result['error_message'])
        return result

    return result
