from translate import Translator


def translate_transcript(text, target_language, source_language="auto"):
    """Translate text using Google Translate API.

    Args:
        text (str): Text to translate.
        target_language (str): Target language to translate to.
        source_language (str): Source language to translate from.

    Returns:
        str: Translated text.
    """

    # translate the text
    translator = Translator(to_lang=target_language, from_lang=source_language)
    translation = translator.translate(text)
    print(f"Translated text: {translation}")
    # return the translated text
    return translation
