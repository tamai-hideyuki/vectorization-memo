FROM node:20

WORKDIR /app
COPY apps/frontend/package*.json ./
RUN npm install
COPY apps/frontend/ ./
EXPOSE 3000  # コンテナ内部では3000
CMD ["npm", "run", "dev"]
