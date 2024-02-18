FROM python:3.11.4-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . app

EXPOSE 5000

ENTRYPOINT ["python", "./app/app.py"]