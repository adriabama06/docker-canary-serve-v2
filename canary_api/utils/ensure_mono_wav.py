import io
from pydub import AudioSegment


def ensure_mono_wav(audio_bytes: bytes) -> bytes:
    # Load audio from bytes using an in-memory buffer
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

    # Convert to mono if it's not already
    if audio.channels > 1:
        audio = audio.set_channels(1)

    # Export the mono audio to an in-memory buffer
    output_buffer = io.BytesIO()
    audio.export(output_buffer, format="wav")

    # Retrieve the byte data from the buffer
    return output_buffer.getvalue()
