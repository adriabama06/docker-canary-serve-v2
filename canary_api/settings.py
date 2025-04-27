from pydantic import Field
from pydantic_settings import BaseSettings


class CanarySettings(BaseSettings):
    # Core
    models_path: str = Field("./models", description="Path to the models directory")

    # Model settings
    model_name: str = Field("nvidia/canary-180m-flash", description="Name of the pretrained Canary model")
    beam_size: int = Field(1, description="Beam size for decoding strategy")
    batch_size: int = Field(1, description="Default batch size for transcription")
    pnc: str = Field("yes", description="Punctuation and capitalization: 'yes' or 'no'")
    timestamps: str = Field("no", description="Timestamps in output: 'yes' or 'no'")

    # Long audio settings
    max_chunk_duration_sec: int = Field(10, description="Maximum chunk duration in seconds")

    class Config:
        env_prefix = "CANARY_"
        env_file = ".env"


settings = CanarySettings()
