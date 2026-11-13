from fastapi import FastAPI

from app.core.errors import register_error_handlers
from app.routers import auth

app = FastAPI(title="Posudba opreme")
register_error_handlers(app)
app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}