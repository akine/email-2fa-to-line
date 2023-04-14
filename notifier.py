import imaplib
import email
import re
import requests
import time
from dotenv import load_dotenv
from email.header import decode_header
import os

load_dotenv()

def check_yahoo_email(username, password, subject_to_check):
    mail = imaplib.IMAP4_SSL("imap.mail.yahoo.co.jp", 993)
    mail._encoding = "UTF-8"
    mail.login(username, password)
    mail.select("inbox")

    utf8_subject_to_check = subject_to_check.encode('utf-8')
    search_criteria = f'SUBJECT "{utf8_subject_to_check.decode("utf-8")}"'
    _, data = mail.search("UTF-8", search_criteria)
    email_ids = data[0].split()

    if email_ids:
        latest_email_id = email_ids[-1]
        _, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        raw_subject = msg["subject"]
        decoded_subject = decode_header(raw_subject)
        subject = "".join([t[0].decode(t[1] or "ascii") for t in decoded_subject])

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
            elif part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()

def extract_numbers_from_email_body(body):
    match = re.search(r'<div[^>]*>\s*([\d]{6})\s*</div>', body, re.MULTILINE | re.IGNORECASE)
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

sent_codes = set()

# sent_codes.txtファイルから送信済みのコードを読み込む
sent_codes_file = "sent_codes.txt"
if os.path.exists(sent_codes_file):
    with open(sent_codes_file, "r") as f:
        for line in f:
            sent_codes.add(line.strip())

while True:
    code = check_yahoo_email(username, password, subject_to_check)
    if code:
        # sent_codesに含まれていない場合だけメッセージを送信
        if code not in sent_codes:
            message = f"2段階認証コードが届きました: {code}"
            result = send_line_message(access_token, message)
            if not result:
                print("通知の送信に失敗しました。")
            else:
                print(f"送信成功: {message}")
                # sent_codesに送信済みのコードを追加
                sent_codes.add(code)
                # sent_codes.txtファイルに送信済みのコードを追記
                with open(sent_codes_file, "a") as f:
                    f.write(f"{code}\n")
        else:
            print(f"既に送信済みのコード: {code}")
    else:
        print("2段階認証コードが見つかりませんでした。")
    time.sleep(300)  # 5分ごとにチェック
