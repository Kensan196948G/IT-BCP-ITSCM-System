"""IT-BCP-ITSCM-System Backend API"""

from fastapi import FastAPI

app = FastAPI(
    title="IT-BCP-ITSCM-System",
    description="IT事業継続管理システム API",
    version="0.1.0",
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
