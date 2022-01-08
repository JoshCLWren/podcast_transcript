import pydub
import urllib.request
import pdb


url = "https://traffic.megaphone.fm/ADL8016987494.mp3"
output_file = "/tmp/ageofnapoleon.mp3"
urllib.request.urlretrieve(url, output_file)
song = pydub.AudioSegment.from_mp3(output_file)

wav_file = "/tmp/ageofnapoleon.wav"
song = song.set_channels(1)
song = song.set_frame_rate(16000)
song.export(wav_file, format="wav")
