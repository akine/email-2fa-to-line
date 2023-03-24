import imaplib
import email
import re
import requests
import time

def check_yahoo_email(username, password, subject_to_check):
    mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com")
    mail.login(username, password)
    mail.select("inbox")

    _, data = mail.search(None, "UNSEEN")
    email_ids = data[0].split()

    for email_id in email_ids:
        _, msg_data = mail.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject = msg["subject"]

        if subject_to_check in subject:
            body = get_email_body(msg)
            numbers = extract_numbers_from_email_body(body)
            return numbers
    return None

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()

def extract_numbers_from_email_body(body):
    match = re.search(r"あなたの2段階サインイン用コード:\s*(\d{6})", body)
    if match:
        return match.group(1)
    return None

def send_line_message(access_token, message):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"message": message}
    response = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
    return response.status_code == 200

username = os.getenv("YAHOO_USERNAME")
password = os.getenv("YAHOO_PASSWORD")
subject_to_check = os.getenv("EMAIL_SUBJECT")
access_token = os.getenv("LINE_ACCESS_TOKEN")

while True:
    code = check_yahoo_email(username, password, subject_to_check)
    if code:
        message = f"2段階認証コードが届きました: {code}"
        send_line_message(access_token, message)
    time.sleep(60)  # 1分ごとにチェック
