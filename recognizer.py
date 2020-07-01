"""
Module for speech recognition.
"""

import logging
import coloredlogs
coloredlogs.install()

import speech_recognition as sr

from moviepy.editor import AudioFileClip


class SpeechRecognizer():

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def recognize(self, path_to_file):
        """

        :param path_to_file:
        :return:
        """

        logging.info(f"Speech Recognizer is successfully initialized")

        # Retrieving audio length
        audio_len = AudioFileClip(path_to_file).duration

        with sr.AudioFile(path_to_file) as source:

            # Creating AudioData instance
            audio = self.recognizer.record(source, duration=audio_len)

            # Using Google speech recognition
            logging.info(f"Converting audio into text ...")
            text = self.recognizer.recognize_google(audio, language="en-US")
            print(text)


if __name__ == '__main__':
    speech_recognizer = SpeechRecognizer()
    speech_recognizer.recognize('chrtistian_bale_oscar.wav')
