from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from datetime import datetime
from pathlib import Path
import json
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException

# ==== FastAPI 初期化 ====
BASE_DIR   = Path(__file__).resolve().parent
MEMOS_ROOT = BASE_DIR / "memos"

app = FastAPI(
    title="Vectorization Memo API",
    description="メタ付きテキストファイルを `./memos/` に保存する API + 検索機能",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ==== メモ作成エンドポイント ====
@app.post("/api/memo", summary="メモを作成して保存")
async def create_memo(
    category: str = Form(..., description="カテゴリ名"),
    title:    str = Form(..., description="メモのタイトル"),
    tags:     str = Form("",  description="カンマ区切りのタグ"),
    body:     str = Form(..., description="メモ本文"),
):
    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    dirpath = MEMOS_ROOT / category
    dirpath.mkdir(parents=True, exist_ok=True)
    filepath = dirpath / f"{uid}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"UUID: {uid}\n")
        f.write(f"CREATED_AT: {now}\n")
        f.write(f"UPDATED_AT: {now}\n")
        f.write(f"TAGS: {tags}\n")
        f.write(f"CATEGORY: {category}\n\n")
        f.write(f"---\n{title}\n\n{body}")

    return {"message": "saved", "path": str(filepath)}

# ==== インデックス読み込み ====
INDEX_PATH = BASE_DIR / "memos" / "index.faiss"
METAS_PATH = BASE_DIR / "memos" / "metas.json"

if INDEX_PATH.exists() and METAS_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    metas = json.loads((BASE_DIR / "memos" / "metas.json").read_text(encoding="utf-8"))
else:
    index, metas = None, []

# Embedding モデルの準備
search_model = SentenceTransformer("sentence-transformers/LaBSE")
search_model._cpu_count = 0
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

@app.post("/api/search", summary="メモをセマンティック検索")
async def search_memos(
    query: str = Form(..., description="検索クエリ"),
    k:     int = Form(5,   description="取得件数")
):
    if index is None:
        raise HTTPException(status_code=503, detail="Index not built yet. Run embedding.py first.")
    # クエリ埋め込み + L2 正規化
    q_emb = search_model.encode([query], convert_to_numpy=True, normalize_embeddings=False)
    norm = np.linalg.norm(q_emb, axis=1, keepdims=True)
    q_emb = q_emb / np.clip(norm, a_min=1e-12, a_max=None)

    # FAISS 検索
    D, I = index.search(q_emb, k)
    results = []
    for score, idx in zip(D[0], I[0]):
        m = metas[idx]
        results.append({
            "score": float(score),
            "category": m["category"],
            "filename": m["filename"],
            "offset": m["offset"],
            "snippet": m.get("snippet", "")
        })
    return {"results": results}
