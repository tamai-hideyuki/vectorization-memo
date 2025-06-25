from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import asyncio

import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

# ──── CPU スレッド数の設定 ────
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

router = APIRouter()

# ──── ディレクトリ設定 ────
# uvicorn の WORKDIR (--reload でも /app) をプロジェクトルートとして扱う
BASE_DIR         = Path.cwd()
MEMOS_ROOT       = Path(os.getenv("MEMOS_ROOT", BASE_DIR / "memos"))
INDEX_DATA_ROOT  = Path(os.getenv("INDEX_DATA_ROOT", MEMOS_ROOT / ".index_data"))

for d in (MEMOS_ROOT, INDEX_DATA_ROOT):
    if d.exists() and not d.is_dir():
        raise RuntimeError(f"{d} がディレクトリではありません。手動で削除してください。")
    d.mkdir(parents=True, exist_ok=True)

# ──── グローバルリソース ────
search_model: Optional[SentenceTransformer] = None
faiss_index:  Optional[faiss.Index]        = None
meta_list:    List[dict]                   = []
index_lock = asyncio.Lock()


def _normalize(emb: np.ndarray) -> np.ndarray:
    return emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)


async def build_and_save_index():
    """
    全ファイルからインデックスとメタ情報を再構築し、ディスクに保存します。
    """
    global search_model, faiss_index, meta_list

    async with index_lock:
        texts, metas = [], []
        for txt in MEMOS_ROOT.rglob("*.txt"):
            raw = txt.read_text(encoding="utf-8")
            header, body = raw.split("---", 1)
            body = body.strip()

            meta = {
                k.strip(): v.strip()
                for line in header.splitlines() if ": " in line
                for k, v in [line.split(": ", 1)]
            }
            meta.update({
                "category": txt.parent.name,
                "filepath": str(txt),
                "body":     body,
                "snippet":  (body[:100] + "...") if len(body) > 100 else body
            })
            texts.append(body)
            metas.append(meta)

        if not texts:
            faiss_index, meta_list = None, []
            return

        if search_model is None:
            search_model = SentenceTransformer("sentence-transformers/LaBSE")

        emb = search_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False
        ).astype("float32")
        emb = _normalize(emb)

        idx = faiss.IndexFlatL2(emb.shape[1])
        idx.add(emb)

        faiss_index, meta_list = idx, metas
        faiss.write_index(idx, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(metas, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


@router.on_event("startup")
async def on_startup():
    """
    サーバ起動時にモデルロードとインデックス初期化を行います。
    """
    global search_model, faiss_index, meta_list

    # モデルロード（バックグラウンドスレッド）
    search_model = await asyncio.to_thread(
        lambda: SentenceTransformer("sentence-transformers/LaBSE")
    )

    idx_f = INDEX_DATA_ROOT / "index.faiss"
    meta_f = INDEX_DATA_ROOT / "metas.json"
    if idx_f.exists() and meta_f.exists():
        try:
            faiss_index = faiss.read_index(str(idx_f))
            meta_list   = json.loads(meta_f.read_text(encoding="utf-8"))
        except Exception:
            await build_and_save_index()
    else:
        await build_and_save_index()


@router.post("/memo", summary="メモを作成して保存")
async def create_memo(
    category: str = Form(...),
    title:    str = Form(...),
    tags:     str = Form(""),
    body:     str = Form(...),
):
    """
    新規メモを保存し、インクリメンタルにインデックスを更新します。
    """
    global search_model, faiss_index, meta_list

    uid  = uuid4().hex
    now  = datetime.utcnow().isoformat() + "Z"
    catd = MEMOS_ROOT / category
    catd.mkdir(parents=True, exist_ok=True)

    path = catd / f"{uid}.txt"
    content = "\n".join([
        f"UUID: {uid}",
        f"CREATED_AT: {now}",
        f"TITLE: {title}",
        f"TAGS: {tags}",
        f"CATEGORY: {category}",
        "---",
        body
    ])
    path.write_text(content, encoding="utf-8")

    async with index_lock:
        new_meta = {
            "UUID":       uid,
            "CREATED_AT": now,
            "TITLE":      title,
            "TAGS":       tags,
            "CATEGORY":   category,
            "filepath":   str(path),
            "body":       body,
            "snippet":    (body[:100] + "...") if len(body) > 100 else body
        }
        meta_list.append(new_meta)

        if search_model is None:
            search_model = SentenceTransformer("sentence-transformers/LaBSE")

        emb = search_model.encode(
            [body],
            convert_to_numpy=True,
            normalize_embeddings=False
        ).astype("float32")
        emb = _normalize(emb)

        if faiss_index is None:
            await build_and_save_index()
        else:
            faiss_index.add(emb)

        faiss.write_index(faiss_index, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(meta_list, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    return JSONResponse({"message": "saved", "path": str(path)})


@router.post("/search", summary="メモをセマンティック検索")
async def search_memos(query: str = Form(...)):
    """
    クエリを埋め込み、インデックス検索してスコア順に返却します。
    """
    global search_model, faiss_index, meta_list

    if faiss_index is None:
        await build_and_save_index()
        if faiss_index is None:
            raise HTTPException(503, "Index build failed.")

    emb_q = search_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=False
    ).astype("float32")
    emb_q = _normalize(emb_q)

    async with index_lock:
        D, I = faiss_index.search(emb_q, len(meta_list))

    results = []
    for dist, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        m = meta_list[idx]
        score = round(1.0 / (1.0 + float(dist)), 4)
        results.append({
            "uuid":       m.get("UUID", ""),
            "title":      m.get("TITLE", ""),
            "snippet":    m.get("snippet", ""),
            "body":       m.get("body", ""),
            "category":   m.get("CATEGORY", ""),
            "tags":       m.get("TAGS", ""),
            "created_at": m.get("CREATED_AT", ""),
            "score":      score,
        })

    return {"results": sorted(results, key=lambda x: x["score"], reverse=True)}


@router.get("/categories", response_model=List[str], summary="カテゴリ一覧取得")
async def list_categories():
    if faiss_index is None:
        await build_and_save_index()
    return sorted({m["CATEGORY"] for m in meta_list if m.get("CATEGORY")})


@router.get("/tags", response_model=List[str], summary="タグ一覧取得")
async def list_tags():
    if faiss_index is None:
        await build_and_save_index()
    tags = {
        t.strip()
        for m in meta_list
        for t in (m.get("TAGS", "") or "").split(",")
        if t.strip()
    }
    return sorted(tags)
