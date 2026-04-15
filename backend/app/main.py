from fastapi import FastAPI

app = FastAPI(
    title="Multimodal Mental Agent API",
    description="Bootstrap API for Docker Compose validation.",
    version="0.1.0",
)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Multimodal Mental Agent backend is running."}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
