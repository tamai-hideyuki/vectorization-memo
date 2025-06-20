# 名称：vectorization-memo


## 初期ディレクトリ構成案

```text
vectorization-memo/
├── apps/
│   ├── frontend/              # Next.js (UI)
│   │   ├── pages/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── package.json
│   │   └── ... (他の Next.js 設定)
│   ├── backend/               # FastAPI (APIサーバ)
│   │   ├── main.py
│   │   ├── memo_api.py
│   │   ├── requirements.txt
├── docker/                    # Docker関連をすべてここに
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   ├── docker-compose.yml
├── memos/                     # メモ保存ディレクトリ（volumeでマウント）
│   ├── (カテゴリ/uuid.txt)
├── README.md                  # プロジェクト説明

```

## 役割

| ディレクトリ/ファイル     | 役割                                       |
| --------------- | ---------------------------------------- |
| `apps/frontend` | Next.js アプリケーション                         |
| `apps/backend`  | FastAPI アプリケーション                         |
| `docker/`       | すべての Dockerfile と docker-compose.yml を集約 |
| `memos/`        | メモの保存ディレクトリ（ホストと共有）                      |

