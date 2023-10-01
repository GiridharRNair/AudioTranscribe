import os
import uuid
import tempfile
from datetime import date
from flask_cors import CORS
from flask import Flask, request, jsonify
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import openai
from dotenv import load_dotenv
from pydub import AudioSegment
import logging

app = Flask(__name__)
CORS(app)
load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

email_sender = SendGridAPIClient(os.getenv("SENDGRID_KEY"))

ALLOWED_EXTENSIONS = {'mp3', 'mp4', 'mpeg', 'wav', 'flac', 'ogg', 'mpga', 'm4a', 'webm'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def handle_error(message, status_code):
    logger.error(message)
    return jsonify({"error": message}), status_code


@app.route("/transcribe", methods=["POST"])
def transcribe_and_send_email():
    try:
        email = request.form.get('email')
        audio_file = request.files.get('audio_file')

        if not audio_file or not email:
            return handle_error("Missing required fields", 400)

        if not allowed_file(audio_file.filename):
            return handle_error("Invalid File Format", 401)

        unique_filename = str(uuid.uuid4()) + '.' + audio_file.filename.rsplit('.', 1)[1].lower()
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        audio_file.save(upload_path)
        process_transcription(upload_path, email)

        return jsonify({"message": "Transcription request submitted successfully"}), 200

    except Exception as e:
        return handle_error(str(e), 500)


def process_transcription(upload_path, email):
    try:
        full_transcript = transcribe(upload_path)

        if not full_transcript:
            raise Exception("Transcription failed")

        summary = meeting_minutes(full_transcript)

        if not summary:
            raise Exception("Summary generation failed")

        send_email(email, summary, full_transcript)

    except Exception as e:
        logger.error(f"Error in transcription process: {str(e)}")


def send_email(recipient, summary, transcript):
    try:
        subject = f'Transcript - {str(date.today())}'
        message_content = (
            f"Summary: \n{summary['abstract_summary']} \n\n"
            f"Key Points: \n{summary['key_points']} \n\n"
            f"Action Items: \n{summary['action_items']} \n\n"
            f"Sentiment Analysis: \n{summary['sentiment']}\n\n"
            f"Full Transcript:\n{transcript}"
        )

        message = Mail(
            from_email='talktotextpro@gmail.com',
            to_emails=recipient,
            subject=subject,
            plain_text_content=message_content
        )
        email_sender.send(message)
        return jsonify({"message": "Transcription successful"}), 200
    except Exception as e:
        return handle_error(str(e), 500)


def transcribe(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        max_segment_size = 20 * 500

        with tempfile.TemporaryDirectory() as temp_dir:
            segments = []
            transcriptions_segments = []

            start_time = 0
            while start_time < len(audio):
                end_time = min(start_time + max_segment_size, len(audio))
                segment = audio[start_time:end_time]
                temp_file_path = os.path.join(temp_dir, f"segment_{start_time}-{end_time}.wav")
                segment.export(temp_file_path, format="wav")
                segments.append(temp_file_path)
                start_time = end_time

            for segment_path in segments:
                with open(segment_path, 'rb') as segment_file:
                    transcription = openai.Audio.transcribe("whisper-1", segment_file)

                transcriptions_segments.append(transcription['text'])
                os.remove(segment_path)

            full_transcript = ' '.join(transcriptions_segments)
            os.remove(file_path)
            return full_transcript

    except Exception as e:
        logger.error(str(e))
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
            {"role": "system", "content": "You are a highly skilled AI trained in language comprehension and "
                                          "summarization. I would like you to read the following text and summarize "
                                          "it into a concise abstract paragraph. Aim to retain the most important "
                                          "points, providing a coherent and readable summary that could help a person "
                                          "understand the main points of the discussion without needing to read the "
                                          "entire text. Please avoid unnecessary details or tangential points."},
            {"role": "user", "content": transcription}
        ]
    )
    return response['choices'][0]['message']['content']


def key_points_extraction(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "system", "content": "You are a proficient AI with a specialty in distilling information into key"
                                          " points. Based on the following text, identify and list the main points that"
                                          " were discussed or brought up. These should be the most important ideas, "
                                          "findings, or topics that are crucial to the essence of the discussion. Your "
                                          "goal is to provide a list that someone could read to quickly understand what"
                                          " was talked about."},
            {"role": "user", "content": transcription}
        ]
    )
    return response['choices'][0]['message']['content']


def action_item_extraction(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "system", "content": "You are an AI expert in analyzing conversations and extracting action items."
                                          " Please review the text and identify any tasks, assignments, or actions that"
                                          " were agreed upon or mentioned as needing to be done. These could be tasks"
                                          " assigned to specific individuals, or general actions that the group has "
                                          "decided to take. Please list these action items clearly and concisely."},
            {"role": "user", "content": transcription}
        ]
    )
    return response['choices'][0]['message']['content']


def sentiment_analysis(transcription):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "system", "content": "As an AI with expertise in language and emotion analysis, your task is to "
                                          "analyze the sentiment of the following text. Please consider the overall "
                                          "tone of the discussion, the emotion conveyed by the language used, and the "
                                          "context in which words and phrases are used. Indicate whether the sentiment "
                                          "is generally positive, negative, or neutral, and provide brief explanations"
                                          " for your analysis where possible."},
            {"role": "user", "content": transcription}
        ]
    )
    return response['choices'][0]['message']['content']


if __name__ == "__main__":
    app.run()
