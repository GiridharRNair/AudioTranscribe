# TalkToText Backend

This is the README file for the backend of TalkToText, a service that transcribes audio and video files into text. The backend is built using Flask and integrates with various APIs and services to provide transcription functionality.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
- [Usage](#usage)
   - [Transcribing Audio/Video](#transcribing-audiovideo)
   - [Email Notifications](#email-notifications)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Introduction

TalkToText is a service that allows users to transcribe audio and video files into text. The backend of TalkToText is responsible for handling user requests, processing audio/video files, performing transcriptions, and sending email notifications to users with the transcribed content.

The backend utilizes various libraries and services, including Flask, MongoDB, GridFS, SendGrid, and OpenAI's GPT-3 for transcription and summarization.

## Getting Started

### Prerequisites

Before running the TalkToText backend, you'll need to have the following prerequisites installed:

- Python 3.7 or higher
- MongoDB
- OpenAI GPT-3 API Key
- SendGrid API Key

### Installation

1. Clone the TalkToText repository:

   ```shell
   git clone https://github.com/your-username/AudioTranscribe.git
   ```

2. Change to the project directory:

   ```shell
   cd TalkToText-backend
   ```

3. Install the required Python packages:

   ```shell
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file and adding the necessary API keys and configuration:

   ```env
   MONGO_URI=your-mongodb-uri
   OPENAI_KEY=your-openai-api-key
   SENDGRID_KEY=your-sendgrid-api-key
   ```

5. Start the Flask application:

   ```shell
   python application.py
   ```

The backend should now be running at `http://127.0.0.1:5000`.

## Usage

### Transcribing Audio/Video

To transcribe an audio or video file, you can send a POST request to the `/transcribe` endpoint. You need to include the following data in your request:

- `email`: The email address where you want to receive the transcription.
- `file`: The audio or video file to be transcribed.

The backend will process the file, perform the transcription, and send an email to the provided address with a link to access the transcription.

### Email Notifications

The backend uses SendGrid to send email notifications to users. Make sure you have configured SendGrid with a valid API key and sender email address.

## API Endpoints

- `/transcribe` (POST): Transcribes an audio or video file and sends an email notification to the user with the transcription link.
- `/<user_id>/validate` (GET): Initiates the transcription process for a specific user, converts the audio, and sends email notifications.

## Configuration

You can configure the backend by modifying the environment variables in the `.env` file. Some important configuration options include:

- `MONGO_URI`: The MongoDB URI for database storage.
- `OPENAI_KEY`: Your OpenAI GPT-3 API key.
- `SENDGRID_KEY`: Your SendGrid API key.

## Error Handling

The backend handles various error scenarios, such as missing required fields, unsupported file formats, and internal server errors. It returns appropriate JSON responses with error messages and status codes to inform the client of any issues.

## Contributing

We welcome contributions to the TalkToText project. If you'd like to contribute, please fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.