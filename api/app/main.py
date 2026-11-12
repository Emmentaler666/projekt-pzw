from fastapi import FastAPI

app = FastAPI(title="Posudba opreme")


@app.get("/health")
def health():
    return {"status": "ok"}
