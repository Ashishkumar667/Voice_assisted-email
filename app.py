import smtplib
import speech_recognition as sr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dateutil.parser import parse
import os
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Please say the date and time for the meeting (e.g., 'please fix the meeting on 2025-02-23 at 14:30'):")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            logging.info(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            logging.error("Sorry, I could not understand the audio.")
        except sr.RequestError:
            logging.error("Could not request results; check your network connection.")
    return None

def schedule_meeting(date_time_str):
    try:
        meeting_date = parse(date_time_str, fuzzy=True)
        logging.info(f"Meeting scheduled for: {meeting_date}")
        return meeting_date
    except ValueError:
        logging.error("Incorrect date format. Please use a recognized date format.")
        return None

def send_email(meeting_date, recipient_email):
    sender_email = os.environ.get("EMAIL")
    sender_password = os.environ.get("PASSWORD")
    
    if not sender_email or not sender_password:
        logging.error("Email or password environment variables not set.")
        return
    
    subject = "Meeting Scheduled"
    body = f"A meeting has been scheduled for {meeting_date}."
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(os.environ.get('SMTP_SERVER', 'smtp.example.com'), int(os.environ.get('SMTP_PORT', 587)))
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        logging.info("Email sent successfully.")
    except smtplib.SMTPException as e:
        logging.error(f"Failed to send email: {e}")

@app.route('/recognize_speech', methods=['GET'])
def recognize_speech_endpoint():
    text = recognize_speech()
    if text:
        return jsonify({"text": text}), 200
    else:
        return jsonify({"error": "Speech not recognized"}), 400

@app.route('/schedule_meeting', methods=['POST'])
def schedule_meeting_endpoint():
    data = request.json
    date_time_str = data.get('date_time_str')
    meeting_date = schedule_meeting(date_time_str)
    if meeting_date:
        return jsonify({"meeting_date": meeting_date.isoformat()}), 200
    else:
        return jsonify({"error": "Invalid date format"}), 400

@app.route('/send_email', methods=['POST'])
def send_email_endpoint():
    data = request.json
    meeting_date = data.get('meeting_date')
    recipient_email = data.get('recipient_email')
    send_email(meeting_date, recipient_email)
    return jsonify({"message": "Email sent successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)