from fastapi import FastAPI

app = FastAPI(title="Cuestionarios API")


@app.get("/api/health")
def health():
    return {"status": "ok"}
