from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(
    title="Morning AI API",
    description="智能決策系統統管理平台 API",
    version="1.0.0-staging"
)

@app.get("/")
async def root():
    return {"message": "Morning AI API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/readiness")
async def readiness_check():
    return {
        "status": "ok", 
        "ts": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/liveness")
async def liveness_check():
    return {
        "status": "ok",
        "ts": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/db/ping")
async def db_ping():
    # 暫時返回模擬的資料庫連接狀態
    return {
        "db": "ok",
        "ts": datetime.utcnow().isoformat() + "Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
