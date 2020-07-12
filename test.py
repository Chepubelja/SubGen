"""
Module for testing purposes.
"""

from audio_extractor import AudioExtractor
from recognizer import SpeechRecognizer
from sub_generator import SubtitlesGenerator
from translator import SubTranslator



if __name__ == '__main__':
    path_to_video = "christian_bale.mp4"
    path_to_audio = f"{path_to_video.split('.')[0]}.wav"
    path_to_subs = f"{path_to_video.split('.')[0]}.srt"

    audio_ext = AudioExtractor(path_to_video)
    audio_ext.load_video()
    audio_ext.extract_audio()
    audio_ext.save_audio(path_to_audio)

    speech_recognizer = SpeechRecognizer()
    recognized_text = speech_recognizer.recognize('chrtistian_bale_oscar.wav')

    sub_translator = SubTranslator()
    recognized_text = sub_translator.translate(recognized_text, dest_lang='german').text
    # print(recognized_text)

    sub_gen = SubtitlesGenerator(path_to_subs)
    sub_gen.generate_srt(recognized_text)
    # sub_gen.embed_subs_in_video("christian_bale.mp4", "test.mp4")

