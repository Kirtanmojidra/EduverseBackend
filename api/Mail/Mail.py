import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail(to, subject, body,password,username):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "eduverse2401@gmail.com"
    smtp_password = "eovp pawh wxuz grjg"
    from_email = "eduverse2401@gmail.com"
    to_email = to
    subject = f"🎉 Welcome to Eduverse, {username}!"
    body = f"""
          <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Eduverse</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">

    <h1 style="color: #4CAF50; text-align: center;">🎉 Welcome to Eduverse, {username}! 🌟</h1>
    <h1>Use this otp to login : <span style="color:#0000FF">{body}</span></h2>

    <p>Dear <strong>{username}</strong>,</p>

    <p>Aapka Eduverse mein swagat hai! 🎉</p>

    <p>Hum bahut khush hain ki aap ab hamare community ka hissa ban gaye hain. Aapka account successfully create ho chuka hai, aur ab aap sabhi valuable study resources ko access kar sakte hain.</p>

    <h2 style="color: #333;">Aapke account ki details:</h2>

    <ul style="list-style-type: none; padding: 0;">
        <li><strong>Username:</strong> <span style="color: #FF5722;">{username}</span></li>
        <li><strong>Password:</strong> <span style="color: #FF5722;">{password}</span></li>
    </ul>

    <p style="background-color: #f9f9f9; padding: 10px; border-left: 4px solid #4CAF50;">
        Apni login details ko surakshit rakhna mat bhooliye.
    </p>

    <h2 style="color: #333;">Aage kya karein?</h2>

    <ul>
        <li><strong>Resources explore karein:</strong> Abhi browse karna shuru karein aur study materials, old papers aur bhi bahut kuch download karein.</li>
        <li><strong>Documents upload karein:</strong> Apne notes aur resources share karein aur dusre students ki madad karein.</li>
        <li><strong>Bookmark karein:</strong> Apne favorite PDFs aur documents ko save karein easy access ke liye.</li>
    </ul>

    <p>Hum yaha hain aapki academic journey ko aur bhi asaan banane ke liye. Agar aapko kisi bhi tarah ki madad chahiye, toh humein zaroor batayein.</p>

    <p>Eduverse join karne ke liye dhanyavaad, aur happy studying! 📚</p>

    <p>Best regards,</p>
    <p>The Eduverse Team</p>

    <p><a href="https://eduverse-io.vercel.app" style="color: #2196F3; text-decoration: none;">eduverse-io.vercel.app</a></p>

</body>
</html>

            """

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

