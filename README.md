# TalkToText Backend

This is the backend code for TalkToText, an audio transcription service. The application is deployed on Azure using Azure Container App with Docker.

## Configuration

Before running the application, you need to set up the following environment variables in a `.env` file:

```plaintext
OPENAI_KEY=
SENDGRID_KEY=
MONGO_URI=
DOMAIN=
```

- `OPENAI_KEY`: Your OpenAI API key.
- `SENDGRID_KEY`: Your SendGrid API key.
- `MONGO_URI`: MongoDB connection URI.
- `DOMAIN`: The domain where your application is hosted.

## Files and Modules

### `application.py`

This file contains the main Flask application code for TalkToText. It handles audio transcription requests, file uploads, and email notifications.

### `gunicorn_config.py`

The Gunicorn configuration file for running the Flask application. It specifies the host, port, and the number of workers and threads.

### `file_cleanup.py`

A script for cleaning up MongoDB files associated with the application. It is scheduled to run daily using GitHub Actions.

### `Dockerfile`

The Dockerfile for building the Docker image of the application. It installs dependencies, copies the application code, and sets the entry point for running the Flask application.

### `file_cleanup.yaml`

A GitHub Actions workflow file for scheduling the daily execution of the `file_cleanup.py` script to clean up MongoDB files.

### `.github/workflows/flask-aca-app-AutoDeployTrigger-b36526cd-e2fc-4bc1-9c17-c27e37acd542.yml`

A GitHub Actions workflow file for triggering automatic deployments of the Flask application to Azure Container App when changes are pushed to the main branch.

## Usage

1. Set up the required environment variables in a `.env` file.

2. Build the Docker image:

   ```bash
   docker build -t talktotext-backend .
   ```

3. Run the Docker container:

   ```bash
   docker run -p 5000:5000 talktotext-backend
   ```

4. The application will be accessible at `http://localhost:5000`.

## Notes

- The application uses OpenAI for transcription and SendGrid for sending email notifications.
- MongoDB is used to store user information and uploaded audio files.
- The `file_cleanup.py` script is scheduled to run daily to clean up MongoDB files.
- GitHub Actions are set up to automatically deploy the application to Azure Container App when changes are pushed to the main branch.

Please make sure to set up your environment variables and configure the necessary services (OpenAI, SendGrid, Azure, MongoDB) before deploying and using this application.