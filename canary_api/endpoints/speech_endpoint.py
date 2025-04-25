import logging
from typing import Optional
import base64
import os
import wave
from pydantic import BaseModel, ValidationError
from fastapi import APIRouter, UploadFile, Request, HTTPException
from tempfile import NamedTemporaryFile

from canary_api.services.canary_service import CanaryService
from canary_api.utils.split_audio_into_chunks import split_audio_into_chunks
from canary_api.utils.ensure_mono_wav import ensure_mono_wav
from canary_api.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

router = APIRouter()

transcriber = CanaryService()


class ASRRequest(BaseModel):
    file: Optional[str] = None
    language: str = 'en'
    pnc: str = 'yes'
    timestamps: str = 'no'
    beam_size: int = 1
    batch_size: int = 1


def save_temp_audio(data: bytes) -> str:
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp:
        temp.write(data)
        return temp.name


async def process_asr_request(
    audio_bytes: bytes,
    language: str,
    pnc: str,
    timestamps: str,
    beam_size: int,
    batch_size: int
):
    if not audio_bytes or audio_bytes[:4] != b'RIFF':
        logger.error("Invalid audio format (must be WAV)")
        raise HTTPException(400, "Invalid audio format (must be WAV)")

    # Save original audio to temp file
    audio_bytes = ensure_mono_wav(audio_bytes)
    audio_path = save_temp_audio(audio_bytes)

    try:
        transcriber_with_config = CanaryService(beam_size=beam_size)

        # Проверяем совместимость timestamps и flash-модели
        if timestamps == 'yes' and not transcriber_with_config.is_flash_model:
            logger.error("Timestamps requested but model is not flash variant")
            raise HTTPException(400, "Timestamps are only supported with flash models (e.g., canary-1b-flash)")

        # Check duration
        with wave.open(audio_path, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)

        # Long audio, split into chunks
        if duration > settings.max_chunk_duration_sec:
            logger.info(f"Audio longer than 10 sec ({duration:.2f} sec), using chunked inference.")
            chunk_paths = split_audio_into_chunks(audio_path, settings.max_chunk_duration_sec)

            texts = []
            for chunk_path in chunk_paths:
                results = transcriber_with_config.transcribe(
                    audio_input=[chunk_path],
                    batch_size=batch_size,
                    pnc=pnc,
                    timestamps='no',  # timestamps off for now
                    source_lang=language,
                    target_lang=language
                )
                texts.append(results[0].text)
                os.remove(chunk_path)  # remove temp chunk after processing

            full_text = " ".join(texts)
            return {"text": full_text}

        else:
            # Short audio, process as a single file
            results = transcriber_with_config.transcribe(
                audio_input=[audio_path],
                batch_size=batch_size,
                pnc=pnc,
                timestamps=timestamps,
                source_lang=language,
                target_lang=language
            )
            return {"text": results[0].text}

    finally:
        os.remove(audio_path)


@router.post("/inference")
async def asr_endpoint(request: Request):
    content_type = request.headers.get('Content-Type', '')

    try:
        if 'multipart/form-data' in content_type:
            form_data = await request.form()
            input_file: UploadFile = form_data.get('file')
            if not input_file or not input_file.filename.lower().endswith('.wav'):
                logger.error("Missing or invalid WAV file")
                raise HTTPException(400, "Missing or invalid WAV file")

            audio_bytes = await input_file.read()
            language = form_data.get('language', 'en')
            pnc = form_data.get('pnc', 'yes')
            timestamps = form_data.get('timestamps', 'no')
            beam_size = int(form_data.get('beam_size', 1))
            batch_size = int(form_data.get('batch_size', 1))

            return await process_asr_request(
                audio_bytes,
                language,
                pnc,
                timestamps,
                beam_size,
                batch_size
            )

        elif 'application/json' in content_type:
            json_data = await request.json()

            request_data = ASRRequest(**json_data)
            if not request_data.file:
                logger.error("Missing or invalid WAV file")
                raise HTTPException(400, "Missing file")

            audio_bytes = base64.b64decode(request_data.file)

            return await process_asr_request(
                audio_bytes,
                request_data.language,
                request_data.pnc,
                request_data.timestamps,
                request_data.beam_size,
                request_data.batch_size
            )

        else:
            logger.error("Unsupported media type")
            raise HTTPException(415, "Unsupported media type")

    except HTTPException as he:
        logger.error(f"Request failed: {str(he)}")
        raise he
    except ValidationError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise HTTPException(500, "Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(router, host="0.0.0.0", port=9000)
