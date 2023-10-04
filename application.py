import os
import uuid
import gridfs
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_limiter import Limiter
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from sendgrid import SendGridAPIClient, Mail
from concurrent.futures import ThreadPoolExecutor
from flask_limiter.util import get_remote_address
from audio_transcriber import process_transcription

executor = ThreadPoolExecutor()
application = Flask(__name__)
CORS(application)
load_dotenv()

media_folder = 'VideoAudioFiles'
os.makedirs(media_folder, exist_ok=True)
application.config['VideoAudioFiles'] = media_folder
application.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
email_sender = SendGridAPIClient(os.environ.get("SENDGRID_KEY"))
mongo_client = MongoClient(os.environ.get('MONGO_URI'))
domain = os.environ.get('DOMAIN')
db = mongo_client.TalkToText
user_info_collection = db["files"]
fs = gridfs.GridFS(db)

limiter = Limiter(
    get_remote_address,
    app=application,
    default_limits=["5 per minute"],
    storage_uri="memory://",
)


@application.route("/transcribe", methods=["POST"])
def transcribe_request():
    try:
        email = request.form.get('email')
        file = request.files.get('file')
        user_uuid = str(uuid.uuid1())

        if not file or not email:
            return jsonify({"error": "Missing required fields"}), 400

        filename = secure_filename(file.filename)

        if accepted_file_ext(filename):
            audio_id = fs.put(file, filename=filename)
        else:
            return jsonify({"error": "Invalid File Format"}), 401

        user_info_collection.insert_one({"email": email, "user_id": user_uuid, "audio_id": audio_id})

        send_email('Audio Transcription Request', email, f'Click here to get your transcription: <a '
                                                         f'href="{domain}/{user_uuid}/validate">Here</a>'
                                                         f"<br /><br /> If you didn't expect this email, just ignore.")

        return jsonify({"message": "Check Your Email"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@application.route('/<user_id>/validate', methods=['GET'])
def transcribe(user_id):
    try:
        user = user_info_collection.find_one({'user_id': user_id})

        if user is None:
            return jsonify({"error": "User not found"}), 404

        audio_file = fs.get(user["audio_id"])

        if audio_file is None:
            return jsonify({"error": "Audio file not found"}), 404

        audio_filename = os.path.join(media_folder, f'{user["audio_id"]}.wav')

        with open(audio_filename, 'wb') as audio_file_out:
            audio_file_out.write(audio_file.read())

        executor.submit(process_transcription, audio_filename, user["email"])

        db['fs.chunks'].delete_many({"files_id": user["audio_id"]})
        fs.delete(user["audio_id"])
        user_info_collection.delete_one({'user_id': user_id})

        return jsonify({"message": "Transcription initiated successfully. "
                                   "You will receive an email with your transcription soon."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@application.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": str(e)}), 429


def accepted_file_ext(filename):
    file_ext = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'mpga', 'mp4', 'mpeg', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[-1] in file_ext


def send_email(subject, recipient, email_content):
    try:
        validate_email = Mail(
            from_email='talktotextpro@gmail.com',
            to_emails=recipient,
            subject=subject,
            html_content=email_content
        )
        email_sender.send(validate_email)
    except Exception as e:
        print(f"Failed to send email to {recipient}. Error: {str(e)}")


if __name__ == "__main__":
    application.run(debug=True)
