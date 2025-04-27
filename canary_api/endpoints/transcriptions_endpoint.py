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

SUPPORTED_LANGUAGES = ['en', 'de', 'fr', 'es']


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
    # Check if language is supported
    if language not in SUPPORTED_LANGUAGES:
        logger.error(f"Unsupported language '{language}'. Must be one of {SUPPORTED_LANGUAGES}")
        raise HTTPException(400, f"Unsupported language '{language}'. Supported languages: {SUPPORTED_LANGUAGES}")

    if not audio_bytes or audio_bytes[:4] != b'RIFF':
        logger.error("Invalid audio format (must be WAV)")
        raise HTTPException(400, "Invalid audio format (must be WAV)")

    # Convert timestamps parameter from string to bool/None
    if timestamps == 'yes':
        timestamps_flag = True
    elif timestamps == 'no' or timestamps is None:
        timestamps_flag = None
    else:
        logger.warning(f"Unknown timestamps value '{timestamps}', defaulting to None")
        timestamps_flag = None

    # Save original audio to temp file
    audio_bytes = ensure_mono_wav(audio_bytes)
    audio_path = save_temp_audio(audio_bytes)

    try:
        transcriber_with_config = CanaryService(beam_size=beam_size)

        # Check if timestamps are requested and if the model supports it
        if timestamps_flag and not transcriber_with_config.is_flash_model:
            logger.error("Timestamps requested but model is not flash variant")
            raise HTTPException(400, "Timestamps are only supported with flash models (e.g., canary-1b-flash)")

        # Check duration
        with wave.open(audio_path, 'rb') as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate)

        texts = []
        timestamps_all = {"word": [], "segment": []}

        if duration > settings.max_chunk_duration_sec:
            logger.info(
                f"Audio longer than {settings.max_chunk_duration_sec} sec ({duration:.2f} sec), using chunked "
                f"inference.")
            chunk_paths = split_audio_into_chunks(audio_path, settings.max_chunk_duration_sec)

            for chunk_path in chunk_paths:
                results = transcriber_with_config.transcribe(
                    audio_input=[chunk_path],
                    batch_size=batch_size,
                    pnc=pnc,
                    timestamps=timestamps_flag,
                    source_lang=language,
                    target_lang=language
                )
                texts.append(results[0].text)

                # Collect timestamps from each chunk
                if timestamps_flag and hasattr(results[0], 'timestamp') and results[0].timestamp:
                    timestamps_all['word'].extend(results[0].timestamp.get('word', []))
                    timestamps_all['segment'].extend(results[0].timestamp.get('segment', []))

                os.remove(chunk_path)  # remove temp chunk after processing

        else:
            # Short audio, process as a single file
            results = transcriber_with_config.transcribe(
                audio_input=[audio_path],
                batch_size=batch_size,
                pnc=pnc,
                timestamps=timestamps_flag,
                source_lang=language,
                target_lang=language
            )
            texts.append(results[0].text)

            if timestamps_flag and hasattr(results[0], 'timestamp') and results[0].timestamp:
                timestamps_all['word'].extend(results[0].timestamp.get('word', []))
                timestamps_all['segment'].extend(results[0].timestamp.get('segment', []))

        full_text = " ".join(texts)

        response = {"text": full_text}

        if timestamps_flag:
            response["timestamps"] = timestamps_all

        return response

    finally:
        os.remove(audio_path)


@router.post("/inference")
async def asr_endpoint(request: Request):
    try:

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

    except HTTPException as he:
        logger.error(f"Request failed: {str(he)}")
        raise he
    except ValidationError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise HTTPException(500, "Internal server error")
