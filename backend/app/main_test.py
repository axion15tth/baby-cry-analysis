from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Baby Cry Analysis API",
    version="1.0.0",
    description="赤ちゃん泣き声解析システム API - Test Version"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Baby Cry Analysis API - Test Version",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "not connected (test mode)",
        "redis": "not connected (test mode)"
    }

@app.get("/api/v1/test")
async def test_endpoint():
    return {
        "message": "API is working!",
        "endpoints": {
            "auth": {
                "register": "POST /api/v1/auth/register (not available in test mode)",
                "login": "POST /api/v1/auth/login (not available in test mode)",
                "me": "GET /api/v1/auth/me (not available in test mode)"
            },
            "files": "Not implemented yet",
            "analysis": "Not implemented yet",
            "export": "Not implemented yet"
        }
    }
