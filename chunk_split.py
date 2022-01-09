from pydub import AudioSegment
from pydub.utils import make_chunks

myaudio = AudioSegment.from_file("The_History_of_London.wav", "wav")
chunk_length_ms = 60000  # pydub calculates in millisec
chunks = make_chunks(myaudio, chunk_length_ms)  # Make chunks of one sec

# Export all of the individual chunks as wav files

for i, chunk in enumerate(chunks):
    chunk_name = "The_History_of_London_{0}.wav".format(i + 1)
    print(f"exporting {chunk_name}")
    chunk.export(chunk_name, format="wav")
