FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p instance

EXPOSE 5000

ENV FLASK_APP=run.py
ENV SECRET_KEY=change-this-in-production

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
