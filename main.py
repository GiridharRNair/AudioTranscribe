import os
import uuid
from pydub import AudioSegment
import tempfile
from datetime import date
from flask_cors import CORS
from flask import Flask, request, jsonify
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import openai
from dotenv import load_dotenv
import certifi
import ssl


ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
CORS(app)

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

email_sender = SendGridAPIClient(os.getenv("SENDGRID_KEY"))

email_template_path = 'transcript_email.html'
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route("/transcribe", methods=["POST"])
def transcribe_and_send_email():
    try:
        email = request.form['email']
        file = request.files['audio_file']

        if 'audio_file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 404

        if file:
            unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)
            transcribe(upload_path, email)
            return jsonify({"message": "Transcription request submitted successfully"}), 200
        else:
            return jsonify({"error": "Invalid file format"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(recipient, summary, transcript):
    subject = f'Transcript - {str(date.today())}'
    content = f"Summary: {summary['abstract_summary']}\n\nKey Points: {summary['key_points']}\n\nAction Items: {summary['action_items']}\n\nSentiment Analysis: {summary['sentiment']}\n\nTranscript:\n{transcript}"
    message = Mail(
        from_email='talktotextpro@gmail.com',
        to_emails=recipient,
        subject=subject,
        plain_text_content=content
    )
    try:
        response = email_sender.send(message)
        return response.status_code
    except Exception as e:
        print(f"Failed to send email to {recipient}. Error: {str(e)}")


def allowed_file(filename):
    allowed_extensions = {'mp3', 'wav', 'flac', 'ogg'}  # Add more extensions as needed
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def transcribe(file_path, email):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(file_path)

        # Set the maximum segment size to 25 MB (25 * 1024 * 1024 bytes)
        max_segment_size = 20 * 500

        # Create a temporary directory to store segments
        with tempfile.TemporaryDirectory() as temp_dir:
            segments = []
            transcriptions_segments = []

            # Split the audio into segments
            start_time = 0
            while start_time < len(audio):
                end_time = min(start_time + max_segment_size, len(audio))
                segment = audio[start_time:end_time]

                # Export the segment to a temporary file
                temp_file_path = os.path.join(temp_dir, f"segment_{start_time}-{end_time}.wav")
                segment.export(temp_file_path, format="wav")

                segments.append(temp_file_path)
                start_time = end_time

            # Process and transcribe each segment
            for segment_path in segments:
                with open(segment_path, 'rb') as segment_file:
                    transcription = openai.Audio.transcribe("whisper-1", segment_file)

                transcriptions_segments.append(transcription['text'])
                os.remove(segment_path)

            # Process the transcription as needed
            summary = meeting_minutes(' '.join(transcriptions_segments))
            send_email(email, summary, transcription['text'])
            os.remove(file_path)

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
