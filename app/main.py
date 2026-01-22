from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from app.glpi.routes import router as glpi_router

app = FastAPI(title="GLPI Integration API", 
              description="API to interact with GLPI", 
              version="1.0.0")
app.include_router(glpi_router)

@app.get("/health", tags=["Health"], name="Health Check")
def health():
    return {"status": "ok"}