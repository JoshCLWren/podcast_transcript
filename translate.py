import googletrans

# init the Google API translator
translator = googletrans.Translator()


def translate_transcript(text, target_language="en", source_language="auto"):
    """Translate text using Google Translate API.

    Args:
        text (str): Text to translate.
        target_language (str): Target language to translate to.
        source_language (str): Source language to translate from.

    Returns:
        str: Translated text.
    """

    # translate the text
    translation = translator.translate(text, dest=target_language, src=source_language)

    # return the translated text
    return translation.text
