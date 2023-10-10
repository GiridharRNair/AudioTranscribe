FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENTRYPOINT ["gunicorn", "-c", "gunicorn_config.py", "application:application"]
