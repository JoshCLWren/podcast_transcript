import pydub
import urllib.request
import pdb
from pydub.playback import play


url = "https://traffic.libsyn.com/secure/5minutehistory/The_History_of_London.mp3"
output_file = "/tmp/The_History_of_London.mp3"
urllib.request.urlretrieve(url, output_file)
song = pydub.AudioSegment.from_mp3(output_file)

wav_file = "The_History_of_London.wav"
song = song.set_channels(1)
song = song.set_frame_rate(16000)
song.export(wav_file, format="wav")
