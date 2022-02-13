import audio_conversion
import transcriber
import feedparser
from rq import Queue
from worker import conn
import time
import pytube

q = Queue(connection=conn)


def feed_transcriber(feed_url):
    """Transcribes an entire rss feed of a podcast."""
    start_time = time.time()
    feed = feedparser.parse(feed_url)

    for item in feed.entries:
        try:

            episode = {
                "audio_url": item.links[1].href,
                "title": item.title,
                "media_type": "podcast",
            }

        except IndexError:
            # some rare early episodes have different indexing or no link to an mp3 and for the purpose of this script we will skip such episodes
            print(
                f"{item.title} has a zero episode or a badly formatted episode in the feed skipping due to formatting errors."
            )
            continue

        try:
            wav_file = audio_conversion.wav_converter(
                episode["audio_url"], episode["title"]
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
        wav_file = audio_conversion.wav_converter(
            episode["audio_url"], episode["title"]
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


def video_transcriber(**kwargs):
    """Transcribes a video file's audio."""
    wav_file = audio_conversion.video_to_audio(kwargs["audio_url"])
    kwargs["title"] = (f"{pytube.YouTube(kwargs['audio_url']).title}",)
    kwargs["path"] = wav_file

    transcriber.get_large_audio_transcription(**kwargs)
