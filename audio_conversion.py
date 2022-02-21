import os
import re
import urllib.request

import pydub
import pytube


def wav_converter(url, title, format="mp3"):
    """
    Converts an audio file to a mono wav file and normalizes it.
    """

    output_file = download_resource(url, title, format)

    try:
        if format == "mp3":
            song = pydub.AudioSegment.from_mp3(output_file)
        else:
            song = pydub.AudioSegment.from_file(f"{output_file}", format=format)
    except:
        raise Exception("Could not convert to wav")

    wav_file = f"tmp/{title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    song = song.normalize()

    os.remove(output_file)

    return song.export(wav_file, format="wav")


def download_resource(url, title, format):
    """Downloads a resource from a url and returns the path to the file."""

    folder_name = f"tmp/{title}"
    if not os.path.isdir("tmp"):
        os.mkdir("tmp")
    if not os.path.isdir(folder_name):
        os.mkdir(f"tmp/{title}")
    output_file = f"{folder_name}/{title}.{format}"
    urllib.request.urlretrieve(url, output_file)

    return output_file


def video_to_audio(url):
    """Prepares and processes a youtube url."""

    stream_url = pytube.YouTube(url).streams.filter(only_audio=True).first().url

    video_object = {
        "title": _youtube_title_formatter(url),
    }

    if stream_url:
        video_object["path"] = wav_converter(
            url=stream_url, title=video_object["title"], format="mp4"
        )
    else:
        video_object["path"] = None

    return video_object


def _youtube_title_formatter(url):
    """Removes all non-alphanumeric characters to aid in file/directory creation for the youtube url conversion process."""

    title = f"{pytube.YouTube(url).title}"

    print(f"Downloading {title}")

    return re.sub(r"[^a-zA-Z0-9]", "", title) if title else "untitled - Error in title"
