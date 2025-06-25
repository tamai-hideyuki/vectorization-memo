from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memo_api        import router as memo_router
from admin_memo_api  import admin_router

app = FastAPI(
    title="Vectorization Memo API",
    version="1.0.0",
    description="メモ保存＋セマンティック検索＋管理用 API",
    openapi_tags=[
        {"name": "memo",  "description": "メモ作成・検索"},
        {"name": "admin", "description": "管理用（インデックス再構築）"},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# /api 以下にメモ関連
app.include_router(
    memo_router,
    prefix="/api",
    tags=["memo"],
)

# /admin 以下に管理用エンドポイント
app.include_router(
    admin_router,
    tags=["admin"],
)
