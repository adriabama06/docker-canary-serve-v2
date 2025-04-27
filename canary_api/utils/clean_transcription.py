import re


def clean_transcription(text: str) -> str:
    # 1. Remove special tokens like<|endoftext|>
    text = re.sub(r"<\|.*?\|>", "", text)

    # 2. Remove long repetitions of one character (e.g., "uuuuuuu")
    text = re.sub(r"(.)\1{5,}", r"\1", text)

    # 3 Remove multiple spaces
    text = re.sub(r"\s{2,}", " ", text)

    # 4. Remove non-printable characters
    text = re.sub(r"[^\x00-\x7F]+", " ", text)

    # 5. Clean up the text
    text = text.strip()

    return text
