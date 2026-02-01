#!/usr/bin/env python3
"""
Check Gmail for Railway deployment notifications
"""
import imaplib
import email
from email.header import decode_header
import os
from datetime import datetime, timedelta

def connect_to_gmail():
    """Connect to Gmail via IMAP."""
    email_address = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not email_address or not app_password:
        print("⚠️  GMAIL_ADDRESS and GMAIL_APP_PASSWORD not set")
        return None

    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(email_address, app_password)
    return imap

def check_railway_emails():
    """Check for recent Railway emails."""
    imap = connect_to_gmail()
    if not imap:
        return []

    try:
        imap.select("INBOX")

        # Search for emails from Railway in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        date_str = one_hour_ago.strftime("%d-%b-%Y")

        _, message_ids = imap.search(None, f'(FROM "railway.app" SINCE "{date_str}")')

        railway_emails = []
        ids = message_ids[0].split()

        for msg_id in ids[-10:]:  # Last 10 Railway emails
            _, msg_data = imap.fetch(msg_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject = msg["Subject"]
                    if subject:
                        decoded = decode_header(subject)[0]
                        if isinstance(decoded[0], bytes):
                            subject = decoded[0].decode(decoded[1] or 'utf-8')
                        else:
                            subject = decoded[0]

                    date = msg["Date"]

                    # Get body snippet
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    body = part.get_payload(decode=True).decode(errors='ignore')[:300]
                                    break
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode(errors='ignore')[:300]
                        except:
                            pass

                    railway_emails.append({
                        "subject": subject,
                        "date": date,
                        "snippet": body
                    })

        return railway_emails

    finally:
        imap.logout()

if __name__ == "__main__":
    print("🔍 Checking for Railway notifications...")
    emails = check_railway_emails()

    if emails:
        print(f"\n✉️  Found {len(emails)} Railway email(s):\n")
        for idx, e in enumerate(emails, 1):
            print(f"{idx}. Subject: {e['subject']}")
            print(f"   Date: {e['date']}")
            if "deployed" in e['subject'].lower() or "success" in e['subject'].lower():
                print("   🎉 DEPLOYMENT SUCCESS!")
            elif "failed" in e['subject'].lower() or "error" in e['subject'].lower():
                print("   ❌ DEPLOYMENT FAILED")
            print()
    else:
        print("\n📭 No Railway emails found in the last hour.")
        print("   Check Railway dashboard: https://railway.app/project/[your-project-id]")
