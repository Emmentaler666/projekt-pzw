from fastapi import FastAPI

from app.core.errors import register_error_handlers

app = FastAPI(title="Posudba opreme")
register_error_handlers(app)


@app.get("/health")
def health():
    return {"status": "ok"}

