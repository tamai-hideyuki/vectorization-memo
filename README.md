# vectorization-memo

ローカル専用の意味検索型メモ管理ツール。  
テキストファイルにメタ情報（UUID／タイムスタンプ／タグ／カテゴリ）を付与して保存し、後で類似度検索できます。

---

## 🔍 主な特徴

- **FastAPI + Next.js**
    - API：FastAPI で `POST /api/memo` → `memos/{category}/{UUID}.txt` に保存
    - UI：Next.js でメモ作成フォームを提供

- **Docker 完全管理**
    - `docker/` 配下に Dockerfile & docker-compose.yml を集約
    - `docker-compose up --build` で UI & API が一発起動

- **テキスト＋ベクトル検索対応（将来）**
    - テキストファイルをそのまま保存
    - 後で Sentence-Transformers + FAISS と組み合わせて「意味検索」を実装可能

- **ローカル完結**
    - データベース不要
    - 自分の PC 上で完結／クラウド不要

---



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

## 再ベクトル化手順
### ./memos/ここにある index.faiss と metas.json に最新のデータを書き込む (PCに優しいコマンドで)

```bash
cd apps/backend

# ① 仮想環境をアクティブに
source ../../.venv/bin/activate

# ② 低負荷モードでインデックス再構築
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TORCH_NUM_THREADS=1 TORCH_NUM_INTEROP_THREADS=1
nice -n 19 python embedding.py \
  --root_dir ../../memos \
  --chunk_size 300 \
  --batch_size 1 \
  --output_dir ../../memos/.index_data

# python3 embedding.py でも OK

# ③ コンテナ再起動
docker restart vectorization-backend
```

