from fastapi import FastAPI
from datetime import datetime
import os
import asyncpg

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@app.get("/readiness")
async def readiness_check():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@app.get("/liveness")
async def liveness_check():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@app.get("/db/ping")
async def db_ping():
    try:
        conn = await asyncpg.connect(os.environ.get("DATABASE_URL"))
        await conn.close()
        return {"db": "ok", "ts": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"db": "error", "detail": str(e), "ts": datetime.utcnow().isoformat()}

