FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn boto3 pymongo python-multipart

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
