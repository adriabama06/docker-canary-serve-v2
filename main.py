from fastapi import FastAPI
from canary_api.endpoints.transcriptions_endpoint import router as asr_router

app = FastAPI(
    title="Nvidia Canary ASR API",
    version="1.0.0",
    description="OpenAI-compatible API for Nvidia Canary models"
)

app.include_router(asr_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
