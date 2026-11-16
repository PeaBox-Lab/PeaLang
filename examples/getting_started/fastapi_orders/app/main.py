from fastapi import FastAPI

app = FastAPI(title="orders")

@app.get("/health")
def health():
    return {"status": "ok", "service": "orders"}
