FROM python:3.11-slim

WORKDIR /app

COPY apps/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend/ ./

# embedding.py 実行権限を付与 (お好みで)
RUN chmod +x embedding.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
