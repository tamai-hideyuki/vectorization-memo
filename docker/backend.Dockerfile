FROM python:3.11

WORKDIR /app
COPY apps/backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY apps/backend/ ./
EXPOSE 8000  # コンテナ内部では8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
