"""
Module for extracting audio file from video file.
"""

from moviepy.editor import VideoFileClip, AudioFileClip


class AudioExtractor():
    """
    Class for extracting audio (.mp3) from video file.
    """

    def __init__(self, filename):
        self.filename = filename

    def load_video(self):
        self.video = VideoFileClip(self.filename)

    def load_mp3(self):
        self.audio = AudioFileClip(self.filename)

    def extract_audio(self):
        self.audio = self.video.audio

    def save_audio(self, audio_path):
        self.audio.write_audiofile(audio_path)
