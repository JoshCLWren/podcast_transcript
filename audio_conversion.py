import pydub
import urllib.request
import pytube
import time


def wav_converter(url, podcast_title):
    """
    Converts an mp3 file to a mono wav file.
    """

    output_file = f"/tmp/{podcast_title}.mp3"
    urllib.request.urlretrieve(url, output_file)
    song = pydub.AudioSegment.from_mp3(output_file)

    wav_file = f"{podcast_title}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    return song.export(wav_file, format="wav")


def video_to_wav(url):
    """
    Converts a youtube file to a mono wav file.
    """
    start_time = time.time()
    stream_url = pytube.YouTube(url).streams.filter(only_audio=True).first().url
    print(f"Downloading {stream_url}")
    output_file = f"{pytube.YouTube(url).title}"
    urllib.request.urlretrieve(stream_url, f"{output_file}.mp4")

    print(f"Converting {stream_url[0].title}.mp4 to {stream_url[0].title}.wav")
    song = pydub.AudioSegment.from_mp3(f"{output_file}.mp4")

    wav_file = f"{output_file}.wav"
    song = song.set_channels(1)
    song = song.set_frame_rate(16000)
    return song.export(wav_file, format="wav")
