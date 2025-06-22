from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uuid, json, faiss, numpy as np, torch, asyncio
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
from memo_api  import router as memo_router

# ディレクトリ初期化
BASE_DIR        = Path(__file__).resolve().parent
MEMOS_ROOT      = BASE_DIR / "memos"
INDEX_DATA_ROOT = BASE_DIR / ".index_data"   # インデックス・メタ専用ディレクトリ
MEMOS_ROOT.mkdir(parents=True, exist_ok=True)
INDEX_DATA_ROOT.mkdir(parents=True, exist_ok=True)

# FastAPI 初期化
app = FastAPI(
    title="Vectorization Memo API",
    description="メモ保存 + セマンティック検索 (自動インデックス再構築)"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(memo_router, prefix="/api")

# グローバルリソース
search_model: SentenceTransformer | None = None
faiss_index:  faiss.Index            | None = None
meta_list:    list[dict]                  = []
index_lock = asyncio.Lock()  # 検索と再構築の排他制御

# --------------------------------------------------
# インデックス構築 & 保存
# --------------------------------------------------
async def build_and_save_index():
    global search_model, faiss_index, meta_list

    async with index_lock:
        print("[INFO]: インデックス再構築開始...")
        texts, metas = [], []
        for file in MEMOS_ROOT.rglob("*.txt"):
            try:
                raw = file.read_text(encoding="utf-8")
                meta_block, body = raw.split("---", 1)
                meta = { k.strip(): v.strip() for k, v in
                         (line.split(": ", 1) for line in meta_block.splitlines() if ": " in line) }
                meta.update({
                    "category": file.parent.name,
                    "filename": file.name,
                    "filepath": str(file),
                })
                texts.append(body.strip())
                metas.append(meta)
            except Exception as e:
                print(f"[WARN]: ファイル解析失敗 {file}: {e}")
        if not texts:
            faiss_index, meta_list = None, []
            print("[INFO]: メモが存在しないためインデックス空設定")
            return

        # モデルロード
        if search_model is None:
            print("[INFO]: SentenceTransformer モデルロード")
            search_model = SentenceTransformer("sentence-transformers/LaBSE")
            search_model._cpu_count = 0
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)

        emb = search_model.encode(texts, convert_to_numpy=True, normalize_embeddings=False, show_progress_bar=True)
        emb /= (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)

        idx = faiss.IndexFlatL2(emb.shape[1])
        idx.add(emb.astype('float32'))

        faiss_index, meta_list = idx, metas
        faiss.write_index(idx, str(INDEX_DATA_ROOT / "index.faiss"))
        (INDEX_DATA_ROOT / "metas.json").write_text(
            json.dumps(metas, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("[INFO]: インデックス再構築 & 保存完了")

# --------------------------------------------------
# サーバ起動時イベント (モデルロードとインデックス初期化)
# --------------------------------------------------
@app.on_event("startup")
async def on_startup():
    global search_model, faiss_index, meta_list

    # シンプルなドットローディング
    async def spin():
        while faiss_index is None:
            print('.', end='', flush=True)
            await asyncio.sleep(1)
    spin_task = asyncio.create_task(spin())

    # モデルロードを非同期実行
    search_model = await asyncio.to_thread(lambda: SentenceTransformer("sentence-transformers/LaBSE"))
    search_model._cpu_count = 0
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)

    # スピナー停止＆完了メッセージ
    spin_task.cancel()
    print("\n[INFO]: モデルロード完了")

    # インデックス読み込み or 再構築
    idx_path, meta_path = INDEX_DATA_ROOT / "index.faiss", INDEX_DATA_ROOT / "metas.json"
    if idx_path.exists() and meta_path.exists():
        try:
            print("[INFO]: 既存インデックス読み込み")
            faiss_index = faiss.read_index(str(idx_path))
            meta_list   = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ERROR]: 読み込み失敗: {e} → 再構築実行")
            await build_and_save_index()
    else:
        print("[INFO]: インデックス未検出 → 構築実行")
        await build_and_save_index()

# --------------------------------------------------
@app.post("/api/search", summary="メモをセマンティック検索")
async def search_memos(query: str = Form(...), k: int = Form(5)):
    if faiss_index is None:
        raise HTTPException(status_code=503, detail="Index not built yet. Please retry later.")

    q = search_model.encode([query], convert_to_numpy=True, normalize_embeddings=False)
    q /= (np.linalg.norm(q, axis=1, keepdims=True) + 1e-12)

    async with index_lock:
        D, I = faiss_index.search(q.astype('float32'), k)

    results = []
    for dist, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        m = meta_list[idx]
        score = round(1 / (1 + dist), 4)
        results.append({
            "score":      score,
            "uuid":       m.get("UUID"),
            "title":      m.get("TITLE"),
            "category":   m.get("category"),
            "filename":   m.get("filename"),
            "created_at": m.get("CREATED_AT"),
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results}
