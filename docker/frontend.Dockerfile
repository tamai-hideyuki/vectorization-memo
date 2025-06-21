FROM node:20-alpine

WORKDIR /app

# 依存インストール
COPY apps/frontend/package*.json ./
RUN npm install

# アプリケーションコピー
COPY apps/frontend/ ./

# ポート公開
EXPOSE 3000

# デフォルトコマンド
CMD ["npm", "run", "dev"]
