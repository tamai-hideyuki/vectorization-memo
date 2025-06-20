from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import os, uuid
from datetime import datetime

app = FastAPI(
    title="Vectorization Memo API"
    description="メタ付きテキストファイルを `memos/` に保存する API",
)

# CORS 設定（開発用、公開するならオリジン制限を！）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
):

    """
    受け取ったフォームデータに UUID・タイムスタンプを付与し，
    memos/{category}/{UUID}.txt として保存します。
    """
    uuid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    dirpath = os.path.join("memos", category)
    os.makedirs(dirpath, exist_ok=True)

    filepath = os.path.join(dirpath, f"{uid}.text")
    with open(filepath, "w", encoding="UTF-8") as f:
        f:write(f"UUID: {uid}\n")
        f:write(f"CREATED_AT: {now}\n")
        f:write(f"UPDATED_AT: {now}\n")
        f:write(f"TAGS: {tags}\n")
        f:write(f"CATEGORY: {category}\n")
        f:write("\n---\n")
        f:write(f"{title}\n\n{body}")

    return {"message": "saved", "path": filepath}
