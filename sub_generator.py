"""
Module for generating subtitles and saving them as .srt file.
"""

import os
import time
import ffmpeg
import subprocess

import logging
import coloredlogs
coloredlogs.install()

from pysrt import SubRipItem, SubRipTime, open as open_srt


class SubtitlesGenerator():

    def __init__(self, srt_path: str):
        self.srt_path = srt_path
        logging.info("Subtitles generator initialized")


    def create_subs_path(self):
        """
        Creates base directory to the result file.
        """

        # Creating base directory
        basedir = os.path.dirname(self.srt_path)
        if not os.path.exists(basedir) and  basedir:
            os.makedirs(basedir)

        # Creating empty file
        with open(self.srt_path, "w") as _:
            pass


    def generate_srt(self, text: str):
        """
        Generates .srt file with the given text and timestamps.
        :param text: String with all retrieved text.
        """
        self.create_subs_path()

        subs = open_srt(self.srt_path)
        texts = self.prepare_text(text.split(" "))
        timestamps = self.prepare_timestamps(texts)

        for i, (sentence, (start_timestamp, end_timestamp)) in enumerate(zip(texts, timestamps)):
            start_timestamp_list = [int(ts) for ts in start_timestamp.split(':')]
            end_timestamp_list = [int(ts) for ts in end_timestamp.split(':')]

            sub = SubRipItem(index=i)
            sub.text = sentence

            sub.start = SubRipTime(hours=start_timestamp_list[0],
                                   minutes=start_timestamp_list[1],
                                   seconds=start_timestamp_list[2],
                                   milliseconds=start_timestamp_list[3])

            sub.end = SubRipTime(hours=end_timestamp_list[0],
                                 minutes=end_timestamp_list[1],
                                 seconds=end_timestamp_list[2],
                                 milliseconds=end_timestamp_list[3])

            subs.append(sub)

        # Saving result subtitles into file
        subs.save(self.srt_path, encoding='utf-8')

        logging.info(f"Generated subtitles are saved in {self.srt_path}")


    def embed_subs_in_video(self, path_to_original, path_to_result):
        """
        Embeds subtitles into a video and saves result as a new video.
        :param path_to_original: Path to original video.
        :param path_to_result: Path to result video.
        """

        subprocess.call(["ffmpeg", "-i", path_to_original, "-i", self.srt_path,
                        "-c:s", "mov_text",  "-c:v",  "copy",  "-c:a", "copy", path_to_result])
        logging.info("Successfully embedded subtitles into video")

    @staticmethod
    def prepare_text(texts: list) -> list:
        if len(texts) % 2 == 0:
            return [" ".join([texts[i], texts[i + 1]]) for i in range(0, len(texts), 2)]
        else:
            return [" ".join([texts[i], texts[i + 1]]) for i in range(0, len(texts[:-1]), 2)] + [texts[-1]]


    @staticmethod
    def prepare_timestamps(texts: list) -> list:
        return [(f"{time.strftime('%H:%M:%S', time.gmtime(i))}:000",
                 f"{time.strftime('%H:%M:%S', time.gmtime(i + 1))}:000")
                for i in range(len(texts) // 2)]


if __name__ == '__main__':

    text = "hello now he came to an award whose previous winners include Jack Nicholson Sean Connery Denzel Washington and have your boredom just to name a few stars were very proud to be called best supporting actor Christian Bale the fighter John Hawkes Winter's Bone Jeremy Renner the town Mark Ruffalo the Kids are Alright The King's Speech and the Oscar goes to Christian Bale the fighter bloody hell yeah I can't wait a listen he's had a wonderful story and I can't wait to see the next chapter of your story you know if it if you want if you want to be a champ if you want to go train with him go meet with him dick Eklund.com go do it check him out ok alright he deserves it produces Mark David incredible related to William paramount just putting this out there and let people know exist so many movies has just brilliant but nobody ever knows about and so was so lucky to be here tonight and have people recognise that my team played by Patrick and boomer and Carlos and Jane and Anna and Julie thank you so much for everything you do and a course mostly my wonderful wife like this is your life I hope I'm likewise to you darling little girl who's told me so much more than a little bit of teacher thank you thank you so much"

    sub_gen = SubtitlesGenerator("sub_results/video_1.srt")
    sub_gen.generate_srt(text)

