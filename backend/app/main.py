from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import auth, audio_files, analysis, export, visualization, users, tags

app = FastAPI(
    title="Baby Cry Analysis API",
    version="1.0.0",
    description="赤ちゃん泣き声解析システム API"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認証"])
app.include_router(audio_files.router, prefix="/api/v1/audio-files", tags=["ファイル管理"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["音声解析"])
app.include_router(export.router, prefix="/api/v1/export", tags=["エクスポート"])
app.include_router(visualization.router, prefix="/api/v1/visualization", tags=["可視化"])
app.include_router(users.router, prefix="/api/v1/users", tags=["ユーザー管理"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["タグ管理"])

@app.get("/")
async def root():
    return {"message": "Baby Cry Analysis API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
