import logging
from pathlib import Path
from nemo.collections.asr.models import EncDecMultiTaskModel

from canary_api.utils.download_model import download_model
from canary_api.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Variable global simple (lazy single-load)
GLOBAL_MODEL = None

class CanaryService:
    """
    A class to handle transcription and translation using the NVIDIA Canary models.
    """

    def __init__(
        self,
        model_name: str = settings.model_name,
        beam_size: int = settings.beam_size
    ):
        global GLOBAL_MODEL
        """
        Initializes the Canary model. Downloads it if not already present locally.
        """
        logger.info(f"Initializing Canary model: {model_name}")

        # Construct full local path
        model_dir = Path(settings.models_path) / model_name
        model_file = model_dir / f"{model_dir.name}.nemo"

        # Download if not exists
        if not model_file.exists():
            logger.info(f"Downloading model: {model_name}")
            Path(download_model(model_name=model_name, local_dir=settings.models_path))

        # Load model from local path
        if GLOBAL_MODEL is None:
            GLOBAL_MODEL = EncDecMultiTaskModel.restore_from(str(model_file))

        self.is_flash_model = "flash" in model_name.lower()

        # Apply decoding strategy
        decode_cfg = GLOBAL_MODEL.cfg.decoding
        decode_cfg.beam.beam_size = beam_size
        GLOBAL_MODEL.change_decoding_strategy(decode_cfg)

    def transcribe(
        self,
        audio_input: list,
        batch_size: int = settings.batch_size,
        pnc: str = settings.pnc,
        timestamps: bool | None = False,
        source_lang: str = 'en',
        target_lang: str = 'en',
    ):
        global GLOBAL_MODEL
        """
        Transcribes or translates the given audio input.
        """
        if not isinstance(audio_input, list):
            raise ValueError("audio_input must be a list of audio file paths.")

        # Fix timestamps value
        if isinstance(timestamps, str):
            if timestamps.lower() == 'yes':
                timestamps = True
            else:
                timestamps = None

        logger.debug({
            "source_lang": source_lang,
            "target_lang": target_lang,
            "batch_size":  batch_size,
            "pnc":         pnc,
            "timestamps":  timestamps
        })

        return GLOBAL_MODEL.transcribe(
            audio_input,
            source_lang=source_lang,
            target_lang=target_lang,
            batch_size=batch_size,
            pnc=pnc,
            timestamps=timestamps
        )


if __name__ == "__main__":
    # Initialize the transcriber
    transcriber = CanaryService()

    # Transcribe a list of audio files
    results = transcriber.transcribe(
        audio_input=['audio1.wav', 'audio2.wav'],
        batch_size=2,
        pnc='yes',
        timestamps=True,
        source_lang='en',
        target_lang='en'
    )

    # Print the transcriptions
    for result in results:
        print(result.text)
