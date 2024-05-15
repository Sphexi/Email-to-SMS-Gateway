# This Python script will check an email account via pop3 every minute and
# send a text message to a phone number if the email account has any unread
# emails. This script will send the text message using the voip.ms REST API,
# and will also check the subject of the email to determine if it is an
# emergency or non-emergency. If the subject of the email matches an item in the env 
# list, the script will send the text message to emergency phone numbers. 
# If the subject of the email is anything else, the script will send the text
# message to a single non-emergency phone number.

import email
import time
import requests
import datetime
import poplib
import os

# Email account settings
EMAIL = os.getenv('EMAIL_USER')
PASSWORD = os.getenv('EMAIL_PASS')
POP3_SERVER = os.getenv('EMAIL_SERVER')
POP3_PORT = 995 # default port for POP3 over SSL


# VOIP.ms settings
VOIP_USERNAME = os.getenv('VOIP_USER')
VOIP_PASSWORD = os.getenv('VOIP_PASS')
VOIP_DID = os.getenv('VOIP_DID')
VOIP_URL = "https://voip.ms/api/v1/rest.php"
VOIP_METHOD = "sendSMS"

# Phone number to send text message to
MAIN_DST = os.getenv('MAIN_DST')
EMERGENCY_DST = os.getenv('EMERGENCY_DST').split(',')
EMERGENCY_PHRASES = os.getenv('EMERGENCY_PHRASES').split(',')

# Time to wait between checking email
WAIT_TIME = os.getenv('WAIT_TIME')

# Function to send text message using the voip.ms REST API
def send_text_message(message, dst):
    response = requests.get(VOIP_URL + "?api_username=" + VOIP_USERNAME + "&api_password=" + VOIP_PASSWORD + "&method=sendSMS&did=" + VOIP_DID + "&dst=" + dst + "&message=" + message[:160])
    return response.text

# Function to decode MIME words
def decode_mime_words(s):
    return u''.join(
        word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        for word, encoding in email.header.decode_header(s))

# Function to check email using POP3
def check_mail_pop3():
    mail = poplib.POP3_SSL(POP3_SERVER, POP3_PORT)
    mail.set_debuglevel(0) #set to 1 to see the debug output
    mail.user(EMAIL)
    mail.pass_(PASSWORD)
    num_messages = len(mail.list()[1])
    email_info = []
    for i in range(num_messages):
        response, raw_email, octets = mail.retr(i + 1)
        email_message = email.message_from_bytes(b'\n'.join(raw_email))
        email_info.append((email_message['From'], decode_mime_words(email_message['Subject']), email_message.get_payload()))
        mail.dele(i + 1) # delete email from server
    mail.quit()
    return email_info

# Main function
def main():
    while True:
        print(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S") + " Checking email...")
        email_info = check_mail_pop3()
        if email_info:
            print("New email found!")
            for email_info in email_info:
                from_address, subject, body = email_info
                print("From:", from_address)
                print("Subject:", subject)
                print("Body:", body)
            print("Sending text message...")
            print("Emergency phrases:", EMERGENCY_PHRASES)
            if subject in EMERGENCY_PHRASES: # emergency
                print("Emergency detected!")
                for dst in EMERGENCY_DST:
                    sms_response = send_text_message(from_address + "\n" + subject + "\n" + (datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")) + "\n\n" + (''.join(str(x) for x in body)), dst)
                    print(sms_response)
            else: # non-emergency
                print("Non-emergency detected!")
                sms_response = send_text_message(from_address + "\n" + subject + "\n" + (datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")) + "\n\n" + (''.join(str(x) for x in body)), MAIN_DST)
                print(sms_response)
        print("Sleeping for " + WAIT_TIME + " seconds...")
        time.sleep(int(WAIT_TIME))

if __name__ == "__main__":
    main()