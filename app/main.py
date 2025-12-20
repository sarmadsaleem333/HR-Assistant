from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="CV Ranking API",
    version="1.0.0"
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
