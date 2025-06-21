FROM python:3.11-slim

WORKDIR /app

# 依存インストール
COPY apps/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY apps/backend/ ./

# インデックス生成スクリプトに実行権限
RUN chmod +x embedding.py

# ポート公開（コメントは行頭に）
EXPOSE 8000

# デフォルトコマンド
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
