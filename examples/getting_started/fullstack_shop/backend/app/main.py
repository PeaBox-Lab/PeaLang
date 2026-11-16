from fastapi import FastAPI

app = FastAPI(title="shop")

@app.get("/health")
def health():
    return {"status": "ok", "service": "shop"}
