# importing libraries
# from https://www.thepythoncode.com/article/using-speech-recognition-to-convert-speech-to-text-python

from numpy import rec
import speech_recognition as sr
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import shutil
import database
from joblib import Parallel, delayed
import time
import asyncio
import os
from pydub import AudioSegment

# create a speech recognition object
recognizer = sr.Recognizer()

# a function that splits the audio file into chunks
# and applies speech recognition
def get_large_audio_transcription(path, **episode):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """

    # open the audio file using pydub
    start_time = time.time()
    sound = AudioSegment.from_wav(path)
    print("Splitting audio file into chunks")
    # split audio sound where silence is 700 miliseconds or more and get chunks

    chunks = split_on_silence(
        sound,
        # experiment with this value for your target audio file
        min_silence_len=500,
        # adjust this per requirement
        silence_thresh=sound.dBFS - 14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=True,
    )

    print("Applying speech recognition on each chunk")
    folder_name = f"{path.name}-audio-chunks"
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    # process each chunk
    result_time = time.time()

    results = Parallel(n_jobs=-1)(
        delayed(chunk_processor)(folder_name, i, chunk)
        for i, chunk in enumerate(chunks)
    )
    end_time = time.time()
    print(
        f"Time to process chunks using {os.cpu_count()} cpu cores: {end_time - result_time}"
    )

    shutil.rmtree(folder_name)

    whole_text = "".join(results)
    whole_text = whole_text.replace("\n", " ")
    episode["transcript"] = whole_text
    _time = end_time - start_time
    print(f"Time taken to transcribe the audio file: {_time}")
    try:
        asyncio.run(_insert_into_db(**episode))
    except Exception as e:
        print("task failed")
        print(e)
        with open(f"{path}.txt", "w") as f:
            f.write(whole_text)
    os.remove(f"{path.name}")


def chunk_processor(folder_name, i, audio_chunk):
    # export audio chunk and save it in
    chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
    print(f"exporting {chunk_filename}")
    audio_chunk.export(chunk_filename, format="wav")
    print("Applying speech recognition on chunk")
    # recognize the chunk
    try:
        return translation_context(chunk_filename)
    except Exception:
        _extracted_from_chunk_processor(chunk_filename, 0.98)
        try:
            return translation_context(chunk_filename, speed=0.98)
        except Exception:
            _extracted_from_chunk_processor(chunk_filename, 0.95)
            try:
                return translation_context(chunk_filename, speed=0.95)
            except Exception:
                return "--"


# TODO Rename this here and in `chunk_processor`
def _extracted_from_chunk_processor(chunk_filename, arg2):
    audio_chunk = speed_change(chunk_filename, arg2)
    audio_chunk.export(chunk_filename, format="wav")


# TODO Rename this here and in `chunk_processor`
def audio_to_text(audio_listened, speed=None):
    text = recognizer.recognize_google(audio_listened)
    if speed:
        text += f" (translated at {speed}x speed)"
    print(text)
    return f"{text.capitalize()}. \n"


async def _insert_into_db(**episode):
    """
    Inserting the episode into the database
    """
    print("Inserting into database")
    return await database.update_transcript(**episode)


def speed_change(_file, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound = AudioSegment.from_file(_file, format="wav")

    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )

    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


def translation_context(chunk_filename, speed=None):
    with sr.AudioFile(chunk_filename) as source:
        audio_listened = recognizer.record(source)
        # try converting it to text

        return audio_to_text(audio_listened, speed)
