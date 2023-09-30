import base64
import os
import io
import uuid
from datetime import date
from flask_cors import CORS
from flask import Flask, request, jsonify
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import openai
from dotenv import load_dotenv
import certifi
import ssl

# Use the certifi certificate bundle for SSL verification
ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
CORS(app)

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

email_sender = SendGridAPIClient(os.getenv("SENDGRID_KEY"))

# Define the path to your HTML email template
email_template_path = 'transcript_email.html'
# Define the upload folder where audio files will be stored
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route("/transcribe", methods=["POST"])
def transcribe_and_send_email():
    try:
        # Get the email address from the request
        email = request.form['email']
        file = request.files['audio_file']

        # Check if an audio or video file was uploaded
        if 'audio_file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 404

        # Check if the file has a valid extension (you can add more extensions)
        if file:
            # Generate a unique filename using UUID
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)

            # Transcribe the saved audio file
            transcript = transcribe(upload_path)

            # Summarize the transcript
            summary = meeting_minutes(transcript)

            # Send the transcript and summary in an email
            send_email(email, summary, transcript)

            return jsonify({"message": "Transcription request submitted successfully"}), 200

        else:
            return jsonify({"error": "Invalid file format"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(recipient, summary, transcript):
    subject = f'Transcript - {str(date.today())}'
    content = f"Summary: {summary['abstract_summary']}\n\nKey Points: {summary['key_points']}\n\nAction Items: {summary['action_items']}\n\nSentiment Analysis: {summary['sentiment']}\n\nTranscript:\n{transcript}"
    message = Mail(
        from_email='yourdailyrundown@gmail.com',
        to_emails=recipient,
        subject=subject,
        plain_text_content=content  # Use plain text content for email
    )
    try:
        response = email_sender.send(message)
        return response.status_code
    except Exception as e:
        print(f"Failed to send email to {recipient}. Error: {str(e)}")


def allowed_file(filename):
    allowed_extensions = {'mp3', 'wav', 'flac', 'ogg'}  # Add more extensions as needed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def transcribe(file_path):
    try:
        # Convert the bytes object to a file-like object
        with open(file_path, 'rb') as audio_file:
            transcription = openai.Audio.transcribe("whisper-1", audio_file)
        return transcription['text']
    except Exception as e:
        print(str(e))
        return None


def meeting_minutes(transcription):
    abstract_summary = abstract_summary_extraction(transcription)
    key_points = key_points_extraction(transcription)
    action_items = action_item_extraction(transcription)
    sentiment = sentiment_analysis(transcription)
    return {
        'abstract_summary': abstract_summary,
        'key_points': key_points,
        'action_items': action_items,
        'sentiment': sentiment
    }


def abstract_summary_extraction(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a highly skilled AI trained in language comprehension and summarization. I would "
                           "like you to read the following text and summarize it into a concise abstract paragraph. "
                           "Aim to retain the most important points, providing a coherent and readable summary that "
                           "could help a person understand the main points of the discussion without needing to read "
                           "the entire text. Please avoid unnecessary details or tangential points."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response['choices'][0]['message']['content']


def key_points_extraction(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a proficient AI with a specialty in distilling information into key points. "
                           "Based on the following text, identify and list the main points that were discussed or "
                           "brought up. These should be the most important ideas, findings, or topics that are crucial "
                           "to the essence of the discussion. Your goal is to provide a list that someone could read "
                           "to quickly understand what was talked about."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response['choices'][0]['message']['content']


def action_item_extraction(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are an AI expert in analyzing conversations and extracting action items. Please review "
                           "the text and identify any tasks, assignments, or actions that were agreed upon or mentioned"
                           " as needing to be done. These could be tasks assigned to specific individuals, or general"
                           " actions that the group has decided to take. Please list these action items clearly and"
                           " concisely."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response['choices'][0]['message']['content']


def sentiment_analysis(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "As an AI with expertise in language and emotion analysis, your task is to analyze the "
                           "sentiment of the following text. Please consider the overall tone of the discussion, "
                           "the emotion conveyed by the language used, and the context in which words and phrases are "
                           "used. Indicate whether the sentiment is generally positive, negative, or neutral, and "
                           "provide brief explanations for your analysis where possible."
            },
            {
                "role": "user",
                "content": transcription
            }
        ]
    )
    return response['choices'][0]['message']['content']


if __name__ == "__main__":
    app.run(debug=True)
