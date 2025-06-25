from fastapi import APIRouter, BackgroundTasks, HTTPException
from pathlib import Path
import json, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime

router = APIRouter(prefix="/admin")
INDEX_DIR = Path(__file__).parent / ".index_data"
IDX_PATH   = INDEX_DIR / "index.faiss"
META_PATH  = INDEX_DIR / "metas.json"
MEMOS_DIR  = Path(__file__).parent / "memos"


from .startup import model, faiss_index, meta_list

def incremental_vectorize():
    # 1) 既存メタから処理済みファイルを把握
    processed = { m["filepath"] for m in meta_list }
    new_metas, new_chunks = [], []
    # 2) ディスク走査 → 新しい txt ファイルのみチャンク化
    for file in MEMOS_DIR.rglob("*.txt"):
        fp = str(file)
        if fp in processed:
            continue
        text = file.read_text(encoding="utf-8")
        if text.startswith("---"):
            _, _, text = text.split("---", 2)
        tokens = text.split()
        # chunk_token_size は固定 or 設定値
        for i in range(0, len(tokens), 300):
            chunk = " ".join(tokens[i:i+300])
            new_chunks.append(chunk)
            new_metas.append({
                "filepath": fp,
                "offset": i,
                "added_at": datetime.utcnow().isoformat()+"Z"
            })

    if not new_chunks:
        return "no-new"

    # 3) 新規チャンクだけ埋め込み
    emb = model.encode(new_chunks, convert_to_numpy=True, normalize_embeddings=False)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    emb = emb / np.clip(norms, a_min=1e-12, a_max=None)
    emb32 = emb.astype("float32")

    # 4) FAISS に追加 & 永続化
    faiss_index.add(emb32)
    faiss.write_index(faiss_index, str(IDX_PATH))

    # 5) meta_list 更新 & 保存
    meta_list.extend(new_metas)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

    return f"added {len(new_chunks)} chunks"

@router.post("/incremental-vectorize")
async def api_incremental_vectorize(bg: BackgroundTasks):
    if model is None or faiss_index is None:
        raise HTTPException(503, "Index or model not loaded")
    # バックグラウンドで実行
    bg.add_task(incremental_vectorize)
    return {"status": "started"}
