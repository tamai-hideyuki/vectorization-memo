#!/usr/bin/env python3
import json, faiss, uuid, os
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Embedding 用モデルインポート
from sentence_transformers import SentenceTransformer

# メモ作成エンドポイント
BASE_DIR   = Path(__file__).resolve().parent.parent
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

@app.post("/api/memo", summary="メモを作成して保存")
async def create_memo(
    category: str = Form(...),
    title:    str = Form(...),
    tags:     str = Form(""),
    body:     str = Form(...),
):
    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    dirpath = MEMOS_ROOT / category
    dirpath.mkdir(parents=True, exist_ok=True)
    filepath = dirpath / f"{uid}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"UUID: {uid}
")
        f.write(f"CREATED_AT: {now}
")
        f.write(f"UPDATED_AT: {now}
")
        f.write(f"TAGS: {tags}
")
        f.write(f"CATEGORY: {category}

")
        f.write(f"---
{title}

{body}")
    return {"message": "saved", "path": str(filepath)}

# FAISS インデックス読み込み (起動時1回)
INDEX_PATH = BASE_DIR / "memos" / "index.faiss"
METAS_PATH = BASE_DIR / "memos" / "metas.json"

if INDEX_PATH.exists() and METAS_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    metas = json.loads(METAS_PATH.read_text(encoding="utf-8"))
else:
    index, metas = None, []

# 埋め込みモデルを初期化 (検索用)
search_model = SentenceTransformer("sentence-transformers/LaBSE")

@app.post("/api/search", summary="メモをセマンティック検索")
async def search_memos(
    query: str = Form(..., description="検索クエリ"),
    k: int   = Form(5,   description="取得件数")
):
    if index is None:
        raise HTTPException(status_code=503, detail="インデックスはまだ構築されていません。まずrebuild_index.pyを実行してください。")
    # クエリを埋め込み + L2正規化
    q_emb = search_model.encode([query], convert_to_numpy=True, normalize_embeddings=False)
    q_norm = q_emb / max((np.linalg.norm(q_emb, axis=1, keepdims=True)), 1e-12)
    # 検索
    D, I = index.search(q_norm, k)
    results = []
    for score, idx in zip(D[0], I[0]):
        m = metas[idx]
        results.append({
            "score": float(score),
            **m,
        })
    return {"results": results}
