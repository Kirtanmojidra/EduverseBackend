import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail(to, subject, body,password):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "eduverse2401@gmail.com"
    smtp_password = "eovp pawh wxuz grjg"
    from_email = "eduverse2401@gmail.com"
    to_email = to
    subject = "Eduverse Sign up"
    body = "Use following otp to login into Eduverse: Otp is "+body

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"error:{e}")
        return False

