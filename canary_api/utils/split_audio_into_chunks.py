import wave
import math
from tempfile import NamedTemporaryFile


def split_audio_into_chunks(audio_path: str, max_chunk_duration_sec: float):
    chunks = []

    with wave.open(audio_path, 'rb') as wav:
        framerate = wav.getframerate()
        n_channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        total_frames = wav.getnframes()
        total_duration = total_frames / framerate

        chunk_frames = int(max_chunk_duration_sec * framerate)
        num_chunks = math.ceil(total_frames / chunk_frames)

        for i in range(num_chunks):
            start_frame = i * chunk_frames
            end_frame = min(start_frame + chunk_frames, total_frames)

            wav.setpos(start_frame)
            frames = wav.readframes(end_frame - start_frame)

            with NamedTemporaryFile(delete=False, suffix=".wav") as chunk_file:
                with wave.open(chunk_file, 'wb') as chunk_wav:
                    chunk_wav.setnchannels(n_channels)
                    chunk_wav.setsampwidth(sampwidth)
                    chunk_wav.setframerate(framerate)
                    chunk_wav.writeframes(frames)

                chunks.append(chunk_file.name)

    return chunks
