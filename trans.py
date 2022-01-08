from vosk import Model, KaldiRecognizer
import wave
import json

model_path = "/vosk-model-en-us-daanzu-20200328"
import pdb

pdb.set_trace()
model = Model(model_path)
wf = wave.open(wav_file, "rb")
rec = KaldiRecognizer(model, wf.getframerate())
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    a = rec.AcceptWaveform(data)
    if (a) and "result" in rec.Result():
        print(json.loads(rec.Result())["text"])
