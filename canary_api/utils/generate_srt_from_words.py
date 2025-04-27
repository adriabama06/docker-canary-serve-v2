import srt
from datetime import timedelta


def generate_srt_from_words(word_timestamps, max_words_per_caption=10, max_duration_per_caption=5.0):
    subtitles = []
    idx = 1
    current_words = []
    start_time = None
    end_time = None

    for word_info in word_timestamps:
        word_start = word_info['start']
        word_end = word_info['end']
        word_text = word_info['word']

        if start_time is None:
            start_time = word_start

        current_words.append(word_text)
        end_time = word_end

        if (len(current_words) >= max_words_per_caption) or (end_time - start_time >= max_duration_per_caption):
            subtitles.append(
                srt.Subtitle(
                    index=idx,
                    start=timedelta(seconds=start_time),
                    end=timedelta(seconds=end_time),
                    content=' '.join(current_words)
                )
            )
            idx += 1
            current_words = []
            start_time = None
            end_time = None

    # Add last group
    if current_words and start_time is not None and end_time is not None:
        subtitles.append(
            srt.Subtitle(
                index=idx,
                start=timedelta(seconds=start_time),
                end=timedelta(seconds=end_time),
                content=' '.join(current_words)
            )
        )

    return srt.compose(subtitles)


if __name__ == "__main__":
    print(generate_srt_from_words([
        {'word': 'Hello', 'start': 0.0, 'end': 0.5},
        {'word': 'world', 'start': 0.5, 'end': 1.0},
        {'word': '!', 'start': 1.0, 'end': 1.5},
        {'word': 'How', 'start': 1.5, 'end': 2.0},
        {'word': 'are', 'start': 2.0, 'end': 2.5},
        {'word': 'you?', 'start': 2.5, 'end': 3.0}
    ]))
