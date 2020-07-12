"""
Module for creating translations
"""

from googletrans import Translator
from googletrans import LANGUAGES

print(LANGUAGES)


class SubTranslator():

    def __init__(self):
        self.translator = Translator()

    def translate(self, text, dest_lang):
        if dest_lang.lower() not in LANGUAGES.values():
            raise ValueError("Selected language is not supported!")

        dest_lang_tag = [lang_tag for lang_tag, lang in LANGUAGES.items() if lang == dest_lang][0]

        translation = self.translator.translate(text, src='en', dest=dest_lang_tag)
        return translation

