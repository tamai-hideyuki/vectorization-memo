from fastapi import APIRouter, Form, HTTPException
from pathlib  import Path
from uuid      import uuid4
from datetime  import datetime

router = APIRouter()
BASE_DIR   = Path(__file__).parent
MEMOS_ROOT = BASE_DIR / "memos"
MEMOS_ROOT.mkdir(exist_ok=True, parents=True)

@router.post("/memo",   summary="メモを作成して保存")
async def create_memo(
    category: str = Form(...),
    title:    str = Form(...),
    tags:     str = Form(""),
    body:     str = Form(...),
):
    uid     = uuid4().hex
    now_iso = datetime.utcnow().isoformat() + "Z"
    dirpath = MEMOS_ROOT / category
    dirpath.mkdir(parents=True, exist_ok=True)

    filepath = dirpath / f"{uid}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"UUID: {uid}\n")
        f.write(f"CREATED_AT: {now_iso}\n")
        f.write(f"TAGS: {tags}\n")
        f.write("\n---\n")
        f.write(f"{title}\n\n{body}\n")

    return {"message": "saved", "path": str(filepath)}
