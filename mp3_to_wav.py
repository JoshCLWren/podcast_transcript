import pydub
import urllib.request
from pydub.playback import play


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
