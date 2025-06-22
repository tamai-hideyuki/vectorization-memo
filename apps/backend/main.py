from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from memo_api import router as memo_router

app = FastAPI(
    title="Vectorization Memo API",
    description="メモ保存 + セマンティック検索"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(memo_router, prefix="/api")
