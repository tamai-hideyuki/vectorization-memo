import json, faiss, numpy as np, asyncio
from pathlib import Path
from sentence_transformers import SentenceTransformer
from memo_api import MEMOS_ROOT, INDEX_DATA_ROOT, index_lock, search_model, faiss_index, meta_list

async def build_and_save_index():
    global search_model, faiss_index, meta_list

    async with index_lock:
        processed = { m["filepath"] for m in meta_list }

        new_texts, new_metas = [], []
        for file in MEMOS_ROOT.rglob("*.txt"):
            fp = str(file)
            if fp in processed:
                continue
            raw = file.read_text(encoding="utf-8")
            header, body = raw.split("---", 1)
            body = body.strip()
            meta = {
                k.strip(): v.strip()
                for line in header.splitlines() if ": " in line
                for k,v in [line.split(": ",1)]
            }
            meta.update({
                "category": file.parent.name,
                "filepath": fp,
                "body":     body,
                "snippet":  (body[:100] + "...") if len(body)>100 else body
            })
            new_texts.append(body)
            new_metas.append(meta)

        if not new_texts:
            return

        if search_model is None:
            search_model = SentenceTransformer("sentence-transformers/LaBSE")

        emb = search_model.encode(
            new_texts, convert_to_numpy=True, normalize_embeddings=False
        )
        emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)

        faiss_index.add(emb.astype("float32"))
        meta_list.extend(new_metas)

        faiss.write_index(faiss_index, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(meta_list, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
