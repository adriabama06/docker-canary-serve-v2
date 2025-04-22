from fastapi import FastAPI
from canary_api.endpoints.speech_endpoint import router as tts_router

app = FastAPI(
    title="Nvidia Canary TTS API",
    version="1.0.0",
    description="OpenAI-compatible API for Nvidia Canary models"
)

app.include_router(tts_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
