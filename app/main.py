from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="HR Assistant for CV Ranking",
    version="1.0.0"
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
