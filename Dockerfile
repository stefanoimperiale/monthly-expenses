FROM python:3-slim

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8443

CMD ["python", "main.py"]
