import os

from pysrt import SubRipItem, SubRipTime, open as open_srt


def create_srt_file(srt_path: str) -> None:
    """
    Creates empty .srt file with the given path.
    :param srt_path: Path to .srt file to save.
    """

    basedir = os.path.dirname(srt_path)
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    with open(srt_path, 'w') as _:
        pass


def generate_srt(srt_path: str, texts: list, timestamps: list) -> None:
    """
    Generates .srt file with the given text and timestamps.
    :param srt_path: Path to .srt file.
    :param texts: List of texts.
    :param timestamps: List of the corresponding timestamps.
    """

    create_srt_file(srt_path)

    subs = open_srt(srt_path)

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

    subs.save(srt_path, encoding='utf-8')




if __name__ == '__main__':
    # create_srt_file("sub_results/video_1.srt")
    result_texts = ["bla bla bla", "bla bla bla 2", "bla bla bla 3"]
    result_timestamps = [("00:00:00:000", "00:00:10:000"), ("00:00:11:000", "00:00:14:000"), ("00:00:18:000", "00:00:21:000")]
    generate_srt("sub_results/video_1.srt", result_texts, result_timestamps)