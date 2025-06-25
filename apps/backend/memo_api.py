from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import faiss
import numpy as np
import asyncio
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from sentence_transformers import SentenceTransformer
import torch

# ──── CPU スレッド数の設定 ────
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

router = APIRouter()

# ──── ディレクトリ設定 ────
BASE_DIR        = Path(__file__).parent
MEMOS_ROOT      = BASE_DIR / "memos"
INDEX_DATA_ROOT = BASE_DIR / ".index_data"

for d in (MEMOS_ROOT, INDEX_DATA_ROOT):
    if d.exists() and not d.is_dir():
        raise RuntimeError(f"{d} がディレクトリではありません。手動で削除してください。")
    d.mkdir(parents=True, exist_ok=True)

# ──── グローバルリソース ────
search_model: Optional[SentenceTransformer] = None
faiss_index:  Optional[faiss.Index]        = None
meta_list:    List[dict]                   = []
index_lock = asyncio.Lock()


async def build_and_save_index():
    """
    全ファイルからインデックスとメタ情報を再構築し、ディスクに保存します。
    """
    global search_model, faiss_index, meta_list

    async with index_lock:
        texts, metas = [], []
        for file in MEMOS_ROOT.rglob("*.txt"):
            raw = file.read_text(encoding="utf-8")
            header, body = raw.split("---", 1)
            body = body.strip()

            meta = {
                k.strip(): v.strip()
                for line in header.splitlines() if ": " in line
                for k, v in [line.split(": ", 1)]
            }
            meta.update({
                "category": file.parent.name,
                "filepath": str(file),
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
        )
        emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)

        idx = faiss.IndexFlatL2(emb.shape[1])
        idx.add(emb.astype("float32"))

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

    # モデルロード
    search_model = await asyncio.to_thread(
        lambda: SentenceTransformer("sentence-transformers/LaBSE")
    )

    idx_path, meta_path = INDEX_DATA_ROOT / "index.faiss", INDEX_DATA_ROOT / "metas.json"
    if idx_path.exists() and meta_path.exists():
        try:
            faiss_index = faiss.read_index(str(idx_path))
            meta_list   = json.loads(meta_path.read_text(encoding="utf-8"))
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
    新規メモを保存し、インクリメンタルにインデックスとメタリストを更新します。
    """
    uid     = uuid4().hex
    now_iso = datetime.utcnow().isoformat() + "Z"
    dirpath = MEMOS_ROOT / category
    dirpath.mkdir(exist_ok=True, parents=True)

    filepath = dirpath / f"{uid}.txt"
    content = "\n".join([
        f"UUID: {uid}",
        f"CREATED_AT: {now_iso}",
        f"TITLE: {title}",
        f"TAGS: {tags}",
        f"CATEGORY: {category}",
        "---",
        body
    ])
    filepath.write_text(content, encoding="utf-8")

    # インクリメンタル更新
    async with index_lock:
        # メタ情報追加
        new_meta = {
            "UUID":       uid,
            "CREATED_AT": now_iso,
            "TITLE":      title,
            "TAGS":       tags,
            "CATEGORY":   category,
            "filepath":   str(filepath),
            "body":       body,
            "snippet":    (body[:100] + "...") if len(body) > 100 else body
        }
        meta_list.append(new_meta)

        # 埋め込みを計算してインデックスに追加
        if search_model is None:
            search_model = SentenceTransformer("sentence-transformers/LaBSE")
        emb = search_model.encode(
            [body],
            convert_to_numpy=True,
            normalize_embeddings=False
        )
        emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
        if faiss_index is None:
            # 初回は全量ビルド
            await build_and_save_index()
        else:
            faiss_index.add(emb.astype("float32"))

        # ディスクに保存
        faiss.write_index(faiss_index, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(meta_list, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    return JSONResponse({"message": "saved", "path": str(filepath)})


@router.post("/search", summary="メモをセマンティック検索")
async def search_memos(query: str = Form(...)):
    """
    クエリを埋め込み、インデックス検索してスコア順に返却します。
    """
    if faiss_index is None:
        await build_and_save_index()
        if faiss_index is None:
            raise HTTPException(503, "Index build failed.")

    q = search_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=False
    )
    q /= (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)

    async with index_lock:
        total = len(meta_list)
        D, I = faiss_index.search(q.astype("float32"), total)

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

    # スコア降順
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results}


@router.get("/categories", response_model=List[str], summary="既存のカテゴリ一覧を取得")
async def list_categories():
    """
    meta_list からユニークなカテゴリをソートして返却します。
    """
    if faiss_index is None:
        await build_and_save_index()
    cats = sorted({ m.get("CATEGORY", "") for m in meta_list if m.get("CATEGORY") })
    return cats


@router.get("/tags", response_model=List[str], summary="既存のタグ一覧を取得")
async def list_tags():
    """
    meta_list の TAGS をパースし、ユニークなタグをソートして返却します。
    """
    if faiss_index is None:
        await build_and_save_index()

    tag_set = set()
    for m in meta_list:
        for raw in (m.get("TAGS", "") or "").split(","):
            t = raw.strip()
            if t:
                tag_set.add(t)
    return sorted(tag_set)
