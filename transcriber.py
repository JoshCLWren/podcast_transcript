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
import re

# create a speech recognition object
recognizer = sr.Recognizer()


# a function that splits the audio file into chunks
# and applies speech recognition
def get_large_audio_transcription(path, language="en-us", **episode):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """

    # open the audio file using pydub
    start_time = time.time()
    sound = AudioSegment.from_wav(path)
    print("Splitting audio file into chunks")
    # split audio sound where silence is 500 milliseconds or more and get chunks

    if os.environ.get("KEEP_SILENCE", "True") == "True":
        silence_value = True
    else:
        silence_value = int(os.environ.get("SILENCE_VALUE", 500))

    chunks = split_on_silence(
        sound,
        # experiment with this value for your target audio file
        min_silence_len=int(os.environ.get("MIN_SILENCE_LEN", 500)),
        # adjust this per requirement
        silence_thresh=sound.dBFS - float(os.environ.get("SILENCE_THRESH", 14)),
        # keep the silence for 1 second, adjustable as well
        keep_silence=silence_value,
    )

    print("Applying speech recognition on each chunk")
    folder_name = _setup(path)
    # process each chunk
    for subscription in ["wit_ai"]:
        result_time = time.time()

        results = Parallel(n_jobs=-1)(
            delayed(chunk_processor)(folder_name, i, chunk, service=subscription, language=language)
            for i, chunk in enumerate(chunks)
        )
        end_time = time.time()
        print(
            f"Time to process chunks using {os.cpu_count()} cpu cores: {end_time - result_time}"
        )

        raw_text = "".join(results)
        whole_text = raw_text.replace("\n", " ")
        paragraphed_text = paragrapher(whole_text)
        episode[f"{subscription}_transcript"] = paragraphed_text
        # publish the transcript to a txt file in the transcripts folder
        with open(f"transcripts/{episode['title']}.txt", "w") as f:
            f.write(paragraphed_text)
        # commit and push the text file to git
        os.system(f"git add {episode['title']}.txt")
        os.system(f"git commit -m '{episode['title']}'")
        os.system("git push")



    episode["redis_job"] = None

    _time = end_time - start_time
    print(f"Time taken to transcribe the audio file: {_time}")

    try:
        asyncio.run(_insert_into_db(**episode))
    except Exception as e:
        _log_error(path, whole_text, e)

    _teardown(path, folder_name)


def paragrapher(text):
    """
    make paragraphs out of the sentences in the text. Every three sentences
    seperated by punctuagion are considered a paragraph. Split on ., !, ?
    """
    # capitalize an use of " i " or " i'" to make it grammatically correct
    text = re.sub(r"(\s+i\s+|\s+i')", " I ", text)
    sentences = text.split(". ")
    paragraphs = [". ".join(sentences[i : i + 12]) for i in range(0, len(sentences), 12)]

    # joint the paragraphs together
    return "\n\n".join(paragraphs)


def _teardown(path, folder_name):
    """teardown folder for audio chunks and tmp folder"""
    shutil.rmtree(folder_name)
    os.remove(f"{path.name}")
    shutil.rmtree("tmp")


def _setup(path):
    """setup folder for audio chunks"""
    folder_name = f"{path.name}-audio-chunks"
    # create a directory to store the audio chunks
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    return folder_name


def _log_error(path, whole_text, e):
    """In the event of an error, log the error and the transcript to a txt file"""
    print("task failed")
    print(e)
    if not os.path.isdir("error_logs"):
        os.mkdir("error_logs")
    with open(f"error_logs/{path}.txt", "w") as f:
        f.write("task failed")
        f.write(str(e))
        f.write(whole_text)


def chunk_processor(folder_name, i, audio_chunk, service="google", language="en-US"):
    """Process each chunk and apply speech recognition"""
    # export audio chunk and save it in
    chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
    print(f"exporting {chunk_filename}")
    audio_chunk.export(chunk_filename, format="wav")
    print("Applying speech recognition on chunk")

    speed = 1.00
    translation = None
    while not translation:
        translation = recursive_translation(
            chunk_filename, speed=speed, service=service, language=language
        )
        print(f"Trying at {speed}x speed")
        speed -= 0.05
        if speed < 0.85:  # not seeing improvements anecdotally below this threshold
            return ""
    return translation


def recursive_translation(chunk_filename, service="google", speed=None, language="en-US"):
    """
    Recursively apply speech recognition on the audio file
    """
    try:
        return translation_context(chunk_filename, speed, service, language)
    except Exception:
        return None


def audio_to_text(audio_listened, service="google", speed=None, language="en-US"):
    """Convert audio to text using wit or google"""
    wit_ai_key = os.getenv("WIT_AI_KEY", "6Y76N33DSO3TAMDSHKFPGIRHNTDI33ZF")
    text = None
    if service == "google":
        text = recognizer.recognize_google(audio_listened, language=language)

    text = recognizer.recognize_wit(audio_listened, key=wit_ai_key)
    if speed != 1.0:
        text += f" (translated at {speed}x speed)"

    return _grammarize(text)


def _grammarize(text):
    """Format the text to be somewhat grammatically correct."""

    punctuation = "?" if text[:3] in ["who", "wha", "whe", "why", "how"] else "."

    return f"{text.capitalize()}{punctuation} "


async def _insert_into_db(**episode):
    """
    Inserting the episode into the database
    """

    print("Inserting into database")
    episode["redis_status"] = "done"
    return await database.update_transcript(**episode)


def speed_change(_file, speed=1.0):
    """Adjust the speed of the audio file"""

    sound = AudioSegment.from_file(_file, format="wav")

    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )

    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


def translation_context(
        chunk_filename,
        service="google",
        speed=None,
        language="en-US",
):
    """A context manager for applying speech recognition"""

    with sr.AudioFile(chunk_filename) as source:
        audio_listened = recognizer.record(source)
        # try converting it to text

        return audio_to_text(audio_listened, speed, service, language)
