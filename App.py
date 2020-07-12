from flask import Flask, render_template, request, flash, redirect, session, jsonify, url_for, send_file
import uuid
import os
from celery import Celery
import time
import shutil
from pytube import YouTube

from audio_extractor import AudioExtractor
from recognizer import SpeechRecognizer
from sub_generator import SubtitlesGenerator
from translator import SubTranslator

app = Flask(__name__)
app.secret_key = "super secret key"

UPLOAD_FOLDER = './files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['CELERY_BROKER_URL'] = 'redis://redis:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://redis:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task(bind=True)
def delete_file(self, filename):
    if os.path.exists(filename):
        os.remove(filename)


@celery.task(bind=True)
def my_task(self, inp_file, lang, res_format):
    path_to_video = os.path.join(app.config['UPLOAD_FOLDER'], inp_file)
    video_name = inp_file.split('.')[0]
    path_to_audio = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_name}.wav")
    path_to_subs = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_name}.srt")

    self.update_state(state='PROGRESS',
                      meta={'status': "Extracting audio ..."})

    audio_ext = AudioExtractor(path_to_video)
    audio_ext.load_video()
    audio_ext.extract_audio()
    audio_ext.save_audio(path_to_audio)

    self.update_state(state='PROGRESS',
                      meta={'status': "Converting audio into text ..."})

    speech_recognizer = SpeechRecognizer()
    recognized_text = speech_recognizer.recognize(path_to_audio)

    if (lang != 'english'):
        sub_translator = SubTranslator()
        recognized_text = sub_translator.translate(recognized_text, dest_lang=lang).text

    self.update_state(state='PROGRESS',
                      meta={'status': "Generated subtitles ..."})

    sub_gen = SubtitlesGenerator(path_to_subs)
    sub_gen.generate_srt(recognized_text)

    result = path_to_subs

    if res_format == 'mp4':

        self.update_state(state='PROGRESS',
                      meta={'status': "Embed subtitles into video ..."})

        path_to_video_with_subs = os.path.join(app.config['UPLOAD_FOLDER'], video_name + "_result.mp4") 
        sub_gen.embed_subs_in_video(path_to_video, path_to_video_with_subs)
        result = path_to_video_with_subs

        os.remove(path_to_subs)

    os.remove(path_to_video)
    os.remove(path_to_audio)

    self.update_state(state='PROGRESS',
                    meta={'status': "Done! "})

    # delete result file from server 10 minutes after returning it to user
    delete_file.apply_async(args=[result,], countdown=600)
    return {'result': result}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = my_task.AsyncResult(task_id)
    response = {
        'state': task.state,
    }

    if task.state not in ('FAILURE', 'PENDING') and 'result' in task.info:
        response['result'] = task.info['result']

    if task.state != 'FAILURE' and 'status' in task.info:
        response['status'] = task.info['status']
    else:
        response['status'] = task.state

    return jsonify(response)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        is_yt_file = 'youtube_field' in request.form and request.form['youtube_field'] 
        is_user_file = 'vid_inp_file' in request.files and request.files['vid_inp_file']

        if not is_yt_file and not is_user_file:
            return redirect(request.url)

        session['uid'] = uuid.uuid4()
        lang = request.form['optradio']
        res_format = request.form['optradio_2']
    
        if is_yt_file:
            yt_file = YouTube(request.form['youtube_field']).streams[0].download(UPLOAD_FOLDER)
            yt_filename = yt_file.split('/')[-1]
            new_filename = str(session['uid']) + '.mp4'
            os.rename(os.path.join(app.config['UPLOAD_FOLDER'], yt_filename), os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            session['original_filename'] = yt_filename.split('.')[0]
            inp_file_name = "{}.{}".format(str(session['uid']), 'mp4')

        else:
            vid_inp_file = request.files['vid_inp_file']
            session['original_filename'] = vid_inp_file.filename.split('.')[0]
            file_ext = vid_inp_file.filename.split('.')[-1]
            if file_ext=='mp3' and res_format == 'mp4':
                flash(u'Invalid result format', 'error')
                return redirect(request.url)
            inp_file_name = "{}.{}".format(str(session['uid']), file_ext)
            vid_inp_file.save(os.path.join(app.config['UPLOAD_FOLDER'], inp_file_name))

        task = my_task.apply_async((inp_file_name, lang, res_format))
        return render_template('index.html', Location=url_for('taskstatus', task_id=task.id))

    return render_template('index.html')


@app.route('/return-files/<path:filename>')
def return_files(filename):
    if os.path.exists(filename):
        return_filename = "{}_result.{}".format(session['original_filename'], filename.split('.')[-1])
        return send_file(filename, attachment_filename = return_filename, as_attachment=True)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.debug = True
    app.run()


