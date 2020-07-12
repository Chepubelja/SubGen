from flask import Flask, render_template, request, flash, redirect, session, jsonify, url_for, send_file
import uuid
import os
from celery import Celery
import time
import shutil

from audio_extractor import AudioExtractor
from recognizer import SpeechRecognizer
from sub_generator import SubtitlesGenerator

UPLOAD_FOLDER = './files'
RESULT_FOLDER = './files'

app = Flask(__name__)
app.secret_key = "super secret key"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

ALLOWED_EXTENSIONS = set(['mp4'])

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@celery.task(bind=True)
def delete_file(self, filename):
    if os.path.exists(filename):
        os.remove(filename)


@celery.task(bind=True)
def my_task(self, inp_file):
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

    self.update_state(state='PROGRESS',
                      meta={'status': "Generated subtitles ..."})

    sub_gen = SubtitlesGenerator(path_to_subs)
    sub_gen.generate_srt(recognized_text)

    # delete intermidiate files
    os.remove(path_to_video)
    os.remove(path_to_audio)

    self.update_state(state='PROGRESS',
                      meta={'status': "Done! "})

    # delete result file from server 10 minutes after returning it to user
    delete_file.apply_async(args=[path_to_subs,], countdown=600)
    return {'result': path_to_subs}

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
        session['uid'] = uuid.uuid4()

        if 'vid_inp_file' not in request.files:
            flash('no input file')
            return redirect(request.url)

        vid_inp_file = request.files['vid_inp_file']

        if vid_inp_file and allowed_file(vid_inp_file.filename):
            file_ext = vid_inp_file.filename.split('.')[-1]
            inp_file_name = "{}.{}".format(str(session['uid']), file_ext)
            vid_inp_file.save(os.path.join(app.config['UPLOAD_FOLDER'], inp_file_name))
            task = my_task.apply_async((inp_file_name,))
            return render_template('index.html', Location=url_for('taskstatus', task_id=task.id))
        else:
            flash('some error occurred')
            return redirect(request.url)
    else:
        return render_template("index.html")

@app.route('/return-files/<path:filename>')
def return_files(filename):
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    return redirect(url_for("index"))

   

if __name__ == "__main__":
    app.debug = True
    app.run()


