from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from datetime import datetime

app = FastAPI(
    title="Vectorization Memo API",
    description="メタ付きテキストファイルを `memos/` に保存する API",
)

# CORS 設定（開発用。公開時はオリジン制限を）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/api/memo", summary="メモを作成して保存")
async def create_memo(
    category: str = Form(..., description="カテゴリ名"),
    title:    str = Form(..., description="メモのタイトル"),
    tags:     str = Form("",  description="カンマ区切りのタグ"),
    body:     str = Form(..., description="メモ本文"),
):
    """
    受け取ったフォームデータに UUID・タイムスタンプを付与し、
    memos/{category}/{UUID}.txt として保存します。
    """
    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    dirpath = os.path.join("memos", category)
    os.makedirs(dirpath, exist_ok=True)

    filepath = os.path.join(dirpath, f"{uid}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"UUID: {uid}\n")
        f.write(f"CREATED_AT: {now}\n")
        f.write(f"UPDATED_AT: {now}\n")
        f.write(f"TAGS: {tags}\n")
        f.write(f"CATEGORY: {category}\n")
        f.write("\n---\n")
        f.write(f"{title}\n\n{body}")

    return {"message": "saved", "path": filepath}
