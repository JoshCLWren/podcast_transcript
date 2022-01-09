import mp3_to_wav
import transcriber
import database
import feedparser


async def feed_transcriber(feed_url):
    """Transcribes an entire rss feed of a podcast."""
    feed = feedparser.parse(feed_url)

    for item in feed.entries:
        try:

            episode = {
                "audio_url": item.links[1].href,
                "podcast_title": feed["feed"]["title"],
                "episode_title": item.title,
                "rss_url": feed_url,
            }

        except IndexError:
            # some rare early episodes have different indexing or no link to an mp3 and for the purpose of this script we will skip such episodes
            print(
                f"{item.title} has a zero episode or a badly formatted episode in the feed skipping due to formatting errors."
            )
            continue

        try:
            wav_file = mp3_to_wav.wav_converter(
                episode["audio_url"], episode["podcast_title"]
            )
        except Exception as e:
            print(e)
            continue

        try:

            transcript_output = transcriber.get_large_audio_transcription(wav_file)

            episode["transcript"] = transcript_output
            await database.insert_transcript(**episode)
        except Exception as e:
            print(e)

            continue


async def episode_transcriber(**episode):
    """Transcribes a single episode of a podcast."""
    import pdb

    pdb.set_trace()
    try:
        wav_file = mp3_to_wav.wav_converter(
            episode["audio_url"], episode["episode_title"]
        )
    except Exception as e:
        print(e)
        return

    try:
        transcript_output = transcriber.get_large_audio_transcription(wav_file)
        episode["transcript"] = transcript_output
        await database.insert_transcript(**episode)
    except Exception as e:
        print(e)

        return
