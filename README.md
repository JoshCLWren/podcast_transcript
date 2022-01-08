# podcast_transcript

Before starting it is required to `brew install ffmpeg`

create python environment `make venv`

install dependencies `make deps-install`

Extract vosk-model-en-us-022 into this folder. The model is found here:
`https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip`

convert an mp3 to a wav file using mp3_to_wav.py

run trans.py to transcribe the audio to text.

