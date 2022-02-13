import pydub
import urllib.request
import pytube
import time
import os
import shutil
import re


def wav_converter(url, title, format="mp3"):
    """
    Converts an audio file to a mono wav file and normalizes it.
    """
    start_time, folder_name, output_file = download_resource(url, title, format)

    try:
        if format == "mp3":
            song = pydub.AudioSegment.from_mp3(output_file)
        else:
            song = pydub.AudioSegment.from_file(f"{output_file}", format=format)
    except:
        raise Exception("Could not convert to wav")

    wav_file = f"{title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    song = song.normalize()
    os.remove(output_file)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time to convert mp3 to wav: {total_time}")
    shutil.rmtree("tmp")
    return song.export(wav_file, format="wav")


def download_resource(url, title, format):
    """Downloads a resource from a url and returns the path to the file."""
    start_time = time.time()

    folder_name = f"tmp/{title}"
    if not os.path.isdir("tmp"):
        os.mkdir("tmp")
    if not os.path.isdir(folder_name):
        os.mkdir(f"tmp/{title}")
    output_file = f"{folder_name}/{title}.{format}"
    urllib.request.urlretrieve(url, output_file)
    download_time = time.time() - start_time
    print(f"Download time: {download_time}")
    return start_time, folder_name, output_file


def video_to_audio(url):
    """
    Prepares a youtube url to be converted to a wav.
    """

    stream_url = pytube.YouTube(url).streams.filter(only_audio=True).first().url
    title = f"{pytube.YouTube(url).title}"
    print(f"Downloading {title}")
    regexed_title = re.sub(r"[^a-zA-Z0-9]", "", title)
    return wav_converter(url=stream_url, title=regexed_title, format="mp4")
