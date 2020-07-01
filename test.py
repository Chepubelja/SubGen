"""
Module for testing purposes.
"""

from audio_extractor import AudioExtractor
from recognizer import SpeechRecognizer
from sub_generator import SubtitlesGenerator



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

    sub_gen = SubtitlesGenerator(path_to_subs)
    sub_gen.generate_srt(recognized_text)

