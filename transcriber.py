import asyncio
import os
import shutil
import time

import speech_recognition as sr
from joblib import Parallel, delayed
from pydub import AudioSegment
from pydub.silence import split_on_silence

import database
from translation_service import translate_transcript

ENGLISH_DIALECTS = [
    "en-us",
    "en-gb",
    "en-au",
    "en-ca",
    "en-nz",
    "en-in",
    "english",
]

recognizer = sr.Recognizer()


def get_large_audio_transcription(
    path, source_language="en-us", target_language="en-us", **episode
):
    """
    Splitting the large audio file into chunks
    and apply speech recognition on each of these chunks
    """

    # open the audio file using pydub
    start_time = time.time()
    sound = AudioSegment.from_wav(path)
    # split audio sound where silence is 500 milliseconds or more and get chunks

    if os.environ.get("KEEP_SILENCE") == "True":
        silence_value = True
    else:
        silence_value = int(os.environ.get("SILENCE_VALUE"))

    chunks = split_on_silence(
        sound,
        # experiment with this value for your target audio file
        min_silence_len=int(os.environ.get("MIN_SILENCE_LEN", 500)),
        # adjust this per requirement
        silence_thresh=sound.dBFS - float(os.environ.get("SILENCE_THRESH", 14)),
        # keep the silence for 1 second, adjustable as well
        keep_silence=silence_value,
    )

    folder_name = _setup(path)
    # process each chunk
    # subscriptions = ["wit_ai", "google"]
    # if source_language.lower() not in ENGLISH_DIALECTS:
    #     subscriptions = subscriptions.pop("google")
    subscriptions = ["google"]  # wit_ai is not working for now
    for subscription in subscriptions:
        results = Parallel(n_jobs=-1)(
            delayed(chunk_processor)(
                folder_name,
                i,
                chunk,
                service=subscription,
                source_language=source_language,
                target_language=target_language,
            )
            for i, chunk in enumerate(chunks)
        )

        whole_text = "".join(results)
        whole_text = whole_text.replace("\n", " ")

        episode[f"{subscription}_transcript"] = whole_text
        episode["redis_status"] = f"{subscription} success"
        asyncio.run(_insert_into_db(**episode))

    episode["redis_status"] = "finished"
    episode["redis_job"] = "n/a"
    try:
        asyncio.run(_insert_into_db(**episode))

        _teardown(path, folder_name)
    except Exception as e:
        _log_error(path, **episode, error=e)

        _teardown(path, folder_name)


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


def _log_error(path, e, **episode):
    """In the event of an error, log the error and the transcript to a txt file"""
    print("task failed")
    print(e)
    if not os.path.isdir("error_logs"):
        os.mkdir("error_logs")
    with open(f"error_logs/{path}.txt", "w") as f:
        f.write("task failed")
        f.write(str(e))
        f.write(str(episode))


def chunk_processor(
    folder_name,
    i,
    audio_chunk,
    service,
    source_language,
    target_language,
):
    """Process each chunk and apply speech recognition"""
    chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
    audio_chunk.export(chunk_filename, format="wav")

    speed = 1.00

    while speed > 0.85:
        transcription = recursive_transcription(
            chunk_filename=chunk_filename,
            service=service,
            speed=speed,
            source_language=source_language,
            target_language=target_language,
        )
        speed -= 0.01
        if transcription:
            return transcription
    return ""


def recursive_transcription(
    chunk_filename,
    speed,
    service,
    source_language,
    target_language,
):
    """
    Recursively apply speech recognition on the audio file
    """

    if speed != 1.0:
        print("*" * 10)
        print(f"speed decreased to: {speed}")
        audio_chunk = speed_change(chunk_filename, speed=speed)
        audio_chunk.export(chunk_filename, format="wav")

    with sr.AudioFile(chunk_filename) as source:
        audio_listened = recognizer.record(source)
        # try converting it to text
        try:
            return audio_to_text(
                audio_listened,
                service=service,
                source_language=source_language,
                target_language=target_language,
            )
        except Exception as e:
            print(e)


def audio_to_text(
    audio_listened,
    service,
    source_language,
    target_language,
):
    """Convert audio to text using wit or google"""

    if service == "google":
        try:
            transcribed_text = recognizer.recognize_google(
                audio_listened, language=source_language
            )
        except Exception as e:
            print(f"error in google {e}")
            return ""
        if target_language != source_language and transcribed_text:

            text = translate_transcript(
                text=transcribed_text,
                target_language=target_language,
                source_language=source_language,
            )

            return _add_grammar(text=text, language=source_language)
        else:
            raise Exception("no text")
    if service == "wit_ai" and source_language in ENGLISH_DIALECTS:
        try:
            wit_transcription = _add_grammar(
                recognizer.recognize_wit(
                    audio_listened, key=os.environ.get("WIT_AI_KEY")
                )
            )
        except Exception as e:
            print(f"wit_ai error: {e}")

            return ""

        if (
            source_language in ENGLISH_DIALECTS
            and target_language not in ENGLISH_DIALECTS
            and wit_transcription
        ):
            return translate_transcript(
                text=wit_transcription, target_language=target_language
            )
        return wit_transcription

    raise Exception("Invalid service")


def _add_grammar(text, language="en-US"):
    """Format english text to be somewhat grammatically correct."""

    if language.lower() in ENGLISH_DIALECTS:
        punctuation = "?" if text[:3] in ["who", "wha", "whe", "why", "how"] else "."
        return f"{text.capitalize()}{punctuation} "
    return text


async def _insert_into_db(**episode):
    """
    Inserting the episode into the database
    """

    await database.update_transcript(**episode)


def speed_change(_file, speed=1.0):
    """Adjust the speed of the audio file"""
    sound = AudioSegment.from_file(_file, format="wav")

    sound_with_altered_frame_rate = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    )

    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
