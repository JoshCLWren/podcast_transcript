from vosk import Model, KaldiRecognizer
import wave
import json
import mp3_to_wav

model_path = "/Users/josh.wren/Code/playground/podcast_transcript/vosk-model-en-us-0.22"

model = Model(model_path)
wav_file = "ageofnapoleon.wav"
wf = wave.open(wav_file, "rb")
rec = KaldiRecognizer(model, wf.getframerate())

transcript = f"{wav_file}:\n"

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    a = rec.AcceptWaveform(data)
    try:
        word = json.loads(rec.Result())["text"]
        if len(word) > 0:
            print(transcript)
            transcript += word + " "

    except Exception as e:
        print(e)
        pass

text_transcript = open(f"{wav_file}.txt", "w")

text_transcript.write(transcript)
text_transcript.close()
