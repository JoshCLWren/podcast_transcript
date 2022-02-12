# importing libraries
# from https://www.thepythoncode.com/article/using-speech-recognition-to-convert-speech-to-text-python

import speech_recognition as sr
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import shutil
import database
from joblib import Parallel, delayed
import time
from rq import Queue
from worker import conn
import asyncio
import os

# create a speech recognition object
r = sr.Recognizer()
q = Queue(connection=conn)
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
        keep_silence=500,
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
    print(f"Time to process chunks using {os.cpu_count()}: {end_time - result_time}")

    # return the text for all chunks detected
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
    # the `folder_name` directory.

    chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
    print(f"exporting {chunk_filename}")
    audio_chunk.export(chunk_filename, format="wav")
    print("Applying speech recognition on chunk")
    # recognize the chunk
    with sr.AudioFile(chunk_filename) as source:
        audio_listened = r.record(source)
        # try converting it to text
        try:
            text = r.recognize_google(audio_listened)
            print(text)
            return f"{text.capitalize()}. \n"
        except sr.UnknownValueError as e:
            return f"error: {e}"
        except sr.RequestError as e:
            return f"error: {e}"


async def _insert_into_db(**episode):
    """
    Inserting the episode into the database
    """
    print("Inserting into database")
    return await database.insert_transcript(**episode)
