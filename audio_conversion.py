import pydub
import urllib.request
import pytube
import time
import os
import shutil
import re


def wav_converter(url, podcast_title):
    """
    Converts an mp3 file to a mono wav file.
    """
    start_time = time.time()
    folder_name = f"{podcast_title}"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    output_file = f"/tmp/{podcast_title}.mp3"
    urllib.request.urlretrieve(url, output_file)
    download_time = time.time() - start_time
    print(f"Download time: {download_time}")
    song = pydub.AudioSegment.from_mp3(output_file)

    wav_file = f"{podcast_title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    os.remove(output_file)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time to convert mp3 to wav: {total_time}")
    shutil.rmtree(folder_name)
    return song.export(wav_file, format="wav")


def video_to_wav(url):
    """
    Converts a youtube file to a mono wav file.
    """
    start_time = time.time()

    stream_url = pytube.YouTube(url).streams.filter(only_audio=True).first().url
    title = f"{pytube.YouTube(url).title}"
    print(f"Downloading {title}")
    regexed_title = re.sub(r"[^a-zA-Z0-9]", "", title)
    if not os.path.isdir(regexed_title):
        os.mkdir(regexed_title)
    video_path = os.path.join(regexed_title, f"{regexed_title}")
    urllib.request.urlretrieve(stream_url, video_path)
    download_time = time.time() - start_time
    print(f"Download time: {download_time}")
    print(f"Converting {video_path}.mp4 to {video_path}.wav")
    audio_conversion_start_time = time.time()
    song = pydub.AudioSegment.from_file(f"{video_path}", format="mp4")

    wav_file = f"{regexed_title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    song = song.normalize()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Time to convert mp4 to wav: {audio_conversion_start_time - end_time}")
    print(f"Time to download and convert mp4 to wav: {total_time}")
    shutil.rmtree(regexed_title)
    return song.export(wav_file, format="wav")
