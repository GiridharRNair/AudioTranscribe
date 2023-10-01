# Audio Transcriber Backend

This is the README for the Audio Transcriber Backend, which is a Flask-based application that transcribes audio files and sends the transcription via email. The backend also performs additional processing on the transcription, including summarization, key point extraction, action item identification, and sentiment analysis. Below, you will find information on how to set up and use this backend.

## Prerequisites

Before you can run the Audio Transcriber Backend, make sure you have the following prerequisites installed:

- Python 3.x
- Flask
- Flask-CORS
- SendGrid Python Library
- OpenAI Python Library
- PyDub
- Python `dotenv` library

You also need to set up accounts and obtain API keys for the following services:

- [OpenAI](https://beta.openai.com/signup/)
- [SendGrid](https://sendgrid.com/)

Once you have these prerequisites, replace the placeholders in your `.env` file with your actual API keys.

## Installation

1. Clone this repository to your local machine.

   ```bash
   git clone https://github.com/GiridharRNair/AudioTranscribe.git
   ```

2. Navigate to the project directory.

   ```bash
   cd AudioTranscribe
   ```

3. Create a virtual environment (recommended).

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment.

    - On Windows:

      ```bash
      venv\Scripts\activate
      ```

    - On macOS and Linux:

      ```bash
      source venv/bin/activate
      ```

5. Install the required dependencies.

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask server by running the following command:

   ```bash
   python app.py
   ```

   The server will start at `http://localhost:5000`.

2. Make a POST request to the `/transcribe` endpoint with the following data:

    - `email`: The recipient's email address.
    - `audio_file`: The audio file to be transcribed (supported formats: mp3, mp4, mpeg, wav, flac, ogg, mpga, m4a, webm).

   Example using `curl`:

   ```bash
   curl -X POST -F "email=recipient@example.com" -F "audio_file=@/path/to/audio/file.wav" http://localhost:5000/transcribe
   ```

   This will submit a transcription request. The backend will transcribe the audio, summarize it, extract key points, identify action items, and perform sentiment analysis on the transcription. The results will be emailed to the provided email address.

## Supported Audio Formats

The backend supports the following audio formats for transcription:

- mp3
- mp4
- mpeg
- wav
- flac
- ogg
- mpga
- m4a
- webm

## Customization

- You can customize the AI models used for summarization, key point extraction, action item identification, and sentiment analysis by modifying the respective functions in the `app.py` file.
- You can also customize the email sender's address and the subject line for the email in the `send_email` function.

## Error Handling

- The backend provides error handling for missing required fields, invalid file formats, and internal server errors. Error messages are returned as JSON responses.

## Deployment

For deployment in a production environment, it is recommended to use a production-ready web server like Gunicorn or uWSGI behind a reverse proxy (e.g., Nginx). Ensure proper security measures are in place, such as securing API keys and setting up authentication.

## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) License.