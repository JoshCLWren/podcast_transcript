import pydub
import urllib.request
import pytube
import time
import os
import shutil
import re


def wav_converter(url, title, format="mp3"):
    """
    Converts an audio file to a mono wav file.
    """
    start_time = time.time()
    folder_name = f"{title}"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    output_file = f"/tmp/{title}.mp3"
    urllib.request.urlretrieve(url, output_file)
    download_time = time.time() - start_time
    print(f"Download time: {download_time}")
    if format == "mp3":
        song = pydub.AudioSegment.from_mp3(output_file)
    else:
        song = pydub.AudioSegment.from_file(f"{output_file}", format=format)
    wav_file = f"{title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    song = song.normalize()
    os.remove(output_file)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time to convert mp3 to wav: {total_time}")
    shutil.rmtree(folder_name)
    return song.export(wav_file, format="wav")


def video_to_audio(url):
    """
    Converts a youtube file to a mono wav file.
    """

    stream_url = pytube.YouTube(url).streams.filter(only_audio=True).first().url
    title = f"{pytube.YouTube(url).title}"
    print(f"Downloading {title}")
    regexed_title = re.sub(r"[^a-zA-Z0-9]", "", title)
    return wav_converter(stream_url, regexed_title, format="mp4")
