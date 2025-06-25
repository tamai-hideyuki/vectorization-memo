from fastapi import APIRouter
from memo_api import build_and_save_index

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

@admin_router.post(
    "/incremental-vectorize",
    summary="インクリメンタル再ベクトル化をトリガー"
)
async def incremental_vectorize_endpoint():
    # 既存メモを再処理してインデックス再構築
    await build_and_save_index()
    return {"status": "completed"}
