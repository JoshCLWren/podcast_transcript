import asyncio

import feedparser
from rq import Queue

import audio_conversion
import database
import transcriber
from worker import conn

q = Queue(connection=conn)


def feed_transcriber(feed_url):
    """Transcribes an entire rss feed of a podcast."""
    feed = feedparser.parse(feed_url)

    for item in feed.entries:

        try:

            episode = {
                "audio_url": item.links[1].href,
                "title": item.title,
                "media_type": "podcast",
            }

            wav_file = audio_conversion.wav_converter(
                episode["audio_url"], episode["title"]
            )
        except Exception as e:
            _handle_error(e, **episode)
            continue

        try:
            episode["path"] = wav_file
            transcriber.get_large_audio_transcription(**episode)

        except Exception as e:
            _handle_error(e, **episode)

            continue


def episode_transcriber(**episode):
    """Transcribes a single audio file."""

    try:
        wav_file = audio_conversion.wav_converter(
            episode["audio_url"], episode["title"]
        )
    except Exception as e:
        _handle_error(e, **episode)
        return

    try:
        episode["path"] = wav_file
        transcriber.get_large_audio_transcription(**episode)

    except Exception as e:
        _handle_error(e, **episode)

        return


def video_transcriber(**kwargs):
    """Transcribes a video file's audio."""
    try:
        prepared_video = audio_conversion.video_to_audio(kwargs["audio_url"])
    except Exception as error:
        _handle_error(error, **kwargs)
        prepared_video = {"path": None, "title": None}

    kwargs["path"] = prepared_video.get("path")
    kwargs["title"] = prepared_video.get("title")

    try:
        transcriber.get_large_audio_transcription(**kwargs)
    except Exception as error:
        _handle_error(error, **kwargs)


def _handle_error(error, **kwargs):
    """Handles errors and update redis status to failed."""

    kwargs["redis_status"] = "failed"
    kwargs["error_message"] = str(error)
    kwargs["redis_job"] = "n/a"
    print(f"***** Failed to transcribe audio url: {kwargs['audio_url']} *****")
    print(f"***** Error: {error} *****")
    print("***** Updating redis status to failed *****")
    print("***** Updating redis job to n/a *****")
    print("object contains:")
    error_state = asyncio.run(database.update_transcript(**kwargs))
    print(error_state)
    return error_state
