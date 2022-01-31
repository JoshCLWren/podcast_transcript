import mp3_to_wav
import transcriber
import database
import feedparser
from rq import Queue
from worker import conn
from utils import _count_words_at_url
import time

q = Queue(connection=conn)


def feed_transcriber(feed_url):
    """Transcribes an entire rss feed of a podcast."""
    start_time = time.time()
    feed = feedparser.parse(feed_url)

    for item in feed.entries:
        try:

            episode = {
                "audio_url": item.links[1].href,
                "podcast_title": feed["feed"]["title"],
                "episode_title": item.title,
                "rss_url": feed_url,
            }

        except IndexError:
            # some rare early episodes have different indexing or no link to an mp3 and for the purpose of this script we will skip such episodes
            print(
                f"{item.title} has a zero episode or a badly formatted episode in the feed skipping due to formatting errors."
            )
            continue

        try:
            wav_file = mp3_to_wav.wav_converter(
                episode["audio_url"], episode["podcast_title"]
            )
        except Exception as e:
            print(e)
            continue

        try:
            episode["path"] = wav_file
            transcriber.get_large_audio_transcription(**episode)

        except Exception as e:
            print(e)

            continue
    end_time = time.time()
    print(f"Time to transcribe feed: {end_time - start_time}")


def episode_transcriber(**episode):
    """Transcribes a single audio file."""

    try:
        wav_file = mp3_to_wav.wav_converter(
            episode["audio_url"], episode["episode_title"]
        )
    except Exception as e:
        print(e)
        return

    try:
        episode["path"] = wav_file
        transcriber.get_large_audio_transcription(**episode)

    except Exception as e:
        print(e)

        return


def video_transcriber(url):
    """Transcribes a video file's audio."""
    wav_file = mp3_to_wav.video_to_wav(url)
    episode = {
        "audio_url": url,
        "podcast_title": "Fake Podcast",
        "video_title": "Fake Episode",
        "rss_url": "https://fake.com",
        "path": wav_file,
    }
    transcriber.get_large_audio_transcription(**episode)
