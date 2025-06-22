from fastapi import APIRouter, Form, HTTPException
import json
import faiss
import numpy as np
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from sentence_transformers import SentenceTransformer
import torch

# ──── CPU スレッド数の設定（トップレベルで一度だけ） ────
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

router = APIRouter()

# ──── ディレクトリ設定 ────
BASE_DIR        = Path(__file__).parent
MEMOS_ROOT      = BASE_DIR / "memos"
INDEX_DATA_ROOT = BASE_DIR / ".index_data"
MEMOS_ROOT.mkdir(exist_ok=True, parents=True)
INDEX_DATA_ROOT.mkdir(exist_ok=True, parents=True)

# ──── グローバルリソース ────
search_model: SentenceTransformer | None = None
faiss_index:  faiss.Index        | None = None
# meta_list には、各メモの {
#   "UUID": ..., "CREATED_AT": ..., "TITLE": ..., "TAGS": ..., "CATEGORY": ...
#   "BODY": full_body_text
# } という情報を保持します
meta_list:    list[dict]               = []
index_lock = asyncio.Lock()

# ──── インデックス構築 & 保存 ────
async def build_and_save_index():
    global search_model, faiss_index, meta_list

    async with index_lock:
        texts, metas = [], []

        for file in MEMOS_ROOT.rglob("*.txt"):
            try:
                raw    = file.read_text(encoding="utf-8")
                header, body = raw.split("---", 1)
                # ヘッダ部分をパース
                meta = {
                    k.strip(): v.strip()
                    for line in header.splitlines()
                    if ": " in line
                    for k, v in [line.split(": ", 1)]
                }
                # フルボディを保持しておく
                meta["BODY"] = body.strip()
                # カテゴリも保存
                meta["CATEGORY"] = file.parent.name

                texts.append(body.strip())
                metas.append(meta)
            except Exception:
                continue

        if not texts:
            faiss_index, meta_list = None, []
            return

        if search_model is None:
            search_model = SentenceTransformer("sentence-transformers/LaBSE")

        # 埋め込み＋L2正規化
        embeddings = search_model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=True
        )
        embeddings /= (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12)

        # FAISSインデックス構築
        idx = faiss.IndexFlatL2(embeddings.shape[1])
        idx.add(embeddings.astype("float32"))

        # グローバルにセット＆ディスク保存
        faiss_index, meta_list = idx, metas
        faiss.write_index(idx, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(metas, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

# ──── サーバ起動時: モデルロード & インデックス初期化 ────
@router.on_event("startup")
async def on_startup():
    global search_model, faiss_index, meta_list

    # モデルロード
    search_model = await asyncio.to_thread(
        lambda: SentenceTransformer("sentence-transformers/LaBSE")
    )

    # 既存インデックス読み込み or 再構築
    idx_path, meta_path = INDEX_DATA_ROOT / "index.faiss", INDEX_DATA_ROOT / "metas.json"
    if idx_path.exists() and meta_path.exists():
        try:
            faiss_index = faiss.read_index(str(idx_path))
            meta_list   = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            await build_and_save_index()
    else:
        await build_and_save_index()

# ──── API: メモ作成 ────
@router.post("/memo", summary="メモを作成して保存")
async def create_memo(
    category: str = Form(...),
    title:    str = Form(...),
    tags:     str = Form(""),
    body:     str = Form(...),
):
    uid     = uuid4().hex
    now_iso = datetime.utcnow().isoformat() + "Z"
    dirpath = MEMOS_ROOT / category
    dirpath.mkdir(exist_ok=True, parents=True)

    filepath = dirpath / f"{uid}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"UUID: {uid}\n")
        f.write(f"CREATED_AT: {now_iso}\n")
        f.write(f"TITLE: {title}\n")
        f.write(f"TAGS: {tags}\n")
        f.write("---\n")
        f.write(body.strip())

    return {"message": "saved", "path": str(filepath)}

# ──── API: セマンティック検索 ────
@router.post("/search", summary="メモをセマンティック検索")
async def search_memos(
    query: str = Form(...),
    k:     int  = Form(5),
):
    if faiss_index is None:
        raise HTTPException(503, "Index not built yet.")

    # クエリを埋め込み＋正規化
    q = search_model.encode([query], convert_to_numpy=True, normalize_embeddings=False)
    q /= (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)

    async with index_lock:
        D, I = faiss_index.search(q.astype("float32"), k)

    results = []
    for dist32, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        # numpy.float32 → Python float に変換
        dist  = float(dist32)
        score = round(1.0 / (1.0 + dist), 4)
        m     = meta_list[idx]

        # 本文からスニペット（抜粋）を生成
        body = m.get("BODY", "")
        # キーワードを中心に前後30文字を抜き出す例
        pos = body.lower().find(query.lower())
        if pos == -1:
            snippet = body[:60] + ("…" if len(body) > 60 else "")
        else:
            start = max(0, pos - 30)
            end   = min(len(body), pos + len(query) + 30)
            snippet = ("…" if start>0 else "") + body[start:end] + ("…" if end<len(body) else "")

        results.append({
            "uuid":       m.get("UUID",       ""),
            "title":      m.get("TITLE",      ""),
            "category":   m.get("CATEGORY",   ""),
            "tags":       m.get("TAGS",       ""),
            "created_at": m.get("CREATED_AT", ""),
            "snippet":    snippet,
            "score":      score,
        })

    # スコア降順ソート
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results}
