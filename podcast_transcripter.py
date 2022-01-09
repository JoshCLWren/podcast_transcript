import mp3_to_wav
import transcriber
import feedparser


feed = feedparser.parse("http://www.5minutehistory.com/feed/podcast/")


def feed_transcriber(feed):
    """Transcribes an entire rss feed of a podcast."""
    for item in feed.entries:
        import pdb

        # pdb.set_trace()
        try:
            podcast_episode = {
                "audio_url": item.links[1].href,
                "title": item.title,
            }
            print(podcast_episode)
        except IndexError:
            # some rare early episodes have different indexing or no link to an mp3 and for the purpose of this script we will skip such episodes
            print(
                f"{item.title} has a zero episode or a badly formatted episode in the feed skipping due to formatting errors."
            )
            continue

        try:
            wav_file = mp3_to_wav.wav_converter(
                podcast_episode["audio_url"], podcast_episode["title"]
            )
        except Exception as e:
            print(e)
            continue

        try:

            transcript_output = transcriber.get_large_audio_transcription(wav_file)

            text_transcript = open(
                f"5minutehistory/{podcast_episode['title']}_sr.txt", "w"
            )

            text_transcript.write(transcript_output)
            text_transcript.close()
        except Exception as e:
            print(e)

            continue
