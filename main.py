import os
import uuid
import tempfile
from datetime import date
from flask_cors import CORS
from flask import Flask, request, jsonify
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from concurrent.futures import ThreadPoolExecutor
import openai
from dotenv import load_dotenv
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)
executor = ThreadPoolExecutor()
load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

email_sender = SendGridAPIClient(os.getenv("SENDGRID_KEY"))
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route("/transcribe", methods=["POST"])
def transcribe_and_send_email():
    try:
        email = request.form.get('email')
        file = request.files.get('audio_file')

        if not file or not email:
            return jsonify({"error": "Missing required fields"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid File Format"}), 401

        unique_filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)

        full_transcript = transcribe(upload_path)
        transcription = meeting_minutes(full_transcript)
        send_email(email, transcription, full_transcript)

        return jsonify({"message": "Transcription request submitted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_email(recipient, transcription_info, transcript):
    transcript_summary = f"Summary: \n{transcription_info['abstract_summary']} \n\n"
    key_points = f"Key Points: \n{transcription_info['key_points']} \n\n"
    action_items = f"Action Items: \n{transcription_info['action_items']} \n\n"
    transcript_sentiment_analysis = f"Sentiment Analysis: \n{transcription_info['sentiment']}\n\n"
    full_transcript = f"Full Transcript:\n{transcript}"
    try:
        subject = f'Transcript - {str(date.today())}'
        message = Mail(
            from_email='talktotextpro@gmail.com',
            to_emails=recipient,
            subject=subject,
            plain_text_content=transcript_summary+key_points+action_items+transcript_sentiment_analysis+full_transcript
        )
        email_sender.send(message)
        return jsonify({"message": "Transcription successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def allowed_file(filename):
    allowed_extensions = {'mp3', 'mp4', 'mpeg', 'wav', 'flac', 'ogg', 'mpga', 'm4a', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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
        return jsonify({"error": str(e)}), 500


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
    app.run(debug=True)
