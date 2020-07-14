from flask import Flask, render_template, request, flash, redirect, session, jsonify, url_for, send_file
import uuid
import os
from celery import Celery, states
from celery.exceptions import Ignore
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
def process_video(self, inp_file, lang, res_format):
    try:
        path_to_video = os.path.join(app.config['UPLOAD_FOLDER'], inp_file)
        video_name = inp_file.split('.')[0]
        path_to_audio = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_name}.wav")
        path_to_subs = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_name}.srt")

        path_to_result = path_to_subs
        if res_format == 'mp4':
            path_to_result = os.path.join(app.config['UPLOAD_FOLDER'], video_name + "_result.mp4") 

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
            
            self.update_state(state='PROGRESS',
                    meta={'status': "Translating into {} ...".format(lang)})

            sub_translator = SubTranslator()
            recognized_text = sub_translator.translate(recognized_text, dest_lang=lang).text

        self.update_state(state='PROGRESS',
                        meta={'status': "Generating subtitles ..."})

        sub_gen = SubtitlesGenerator(path_to_subs)
        sub_gen.generate_srt(recognized_text)

        if res_format == 'mp4':

            self.update_state(state='PROGRESS',
                        meta={'status': "Embedding subtitles into video ..."})

            sub_gen.embed_subs_in_video(path_to_video, path_to_result)

        self.update_state(state='PROGRESS',
                        meta={'status': "Done! "})

        # delete result file from server 10 minutes after returning it to user
        delete_file.apply_async(args=[path_to_result,], countdown=600)

        return {'result': path_to_result}

    except Exception as e:
        print("ERROR:", getattr(e, 'message', repr(e)))        
        app.logger.info('error occurred ', getattr(e, 'message', repr(e)))

        self.update_state( 
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': getattr(e, 'message', repr(e)),
            })

        if os.path.exists(path_to_result):
            os.remove(path_to_result)

        raise Ignore()

    finally:
        for filepath in [path_to_video, path_to_audio, path_to_subs]:
            if os.path.exists(filepath):
                os.remove(filepath)


@celery.task(bind=True)
def process_audio(self, inp_file, lang):
    try:
        path_to_audio = os.path.join(app.config['UPLOAD_FOLDER'], inp_file)
        audio_name = inp_file.split('.')[0]
        path_to_audio_new = os.path.join(app.config['UPLOAD_FOLDER'], f"{audio_name}.wav")
        path_to_subs = os.path.join(app.config['UPLOAD_FOLDER'], f"{audio_name}.srt")

        self.update_state(state='PROGRESS',
                        meta={'status': "Converting mp3 to wav ..."})

        audio_ext = AudioExtractor(path_to_audio)
        audio_ext.load_mp3()
        audio_ext.save_audio(path_to_audio_new)

        self.update_state(state='PROGRESS',
                        meta={'status': "Converting audio into text ..."})

        speech_recognizer = SpeechRecognizer()
        recognized_text = speech_recognizer.recognize(path_to_audio_new)

        if (lang != 'english'):

            self.update_state(state='PROGRESS',
                        meta={'status': "Translating into {} ...".format(lang)})

            sub_translator = SubTranslator()
            recognized_text = sub_translator.translate(recognized_text, dest_lang=lang).text

        self.update_state(state='PROGRESS',
                        meta={'status': "Generating subtitles ..."})

        sub_gen = SubtitlesGenerator(path_to_subs)
        sub_gen.generate_srt(recognized_text)

        self.update_state(state='PROGRESS',
                        meta={'status': "Done! "})

        # delete result file from server 10 minutes after returning it to user
        delete_file.apply_async(args=[path_to_subs,], countdown=600)

        return {'result': path_to_subs}

    except Exception as e:
        print("ERROR:", getattr(e, 'message', repr(e)))        
        app.logger.info('error occurred ', getattr(e, 'message', repr(e)))

        self.update_state( 
            state=states.FAILURE,
            meta={
                'exc_type': type(e).__name__,
                'exc_message': getattr(e, 'message', repr(e)),
            })

        if os.path.exists(path_to_subs):
            os.remove(path_to_subs)

        raise Ignore()

    finally:
        for filepath in [path_to_audio, path_to_audio_new]:
            if os.path.exists(filepath):
                os.remove(filepath)


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = process_audio.AsyncResult(task_id)
    response = {
        'state': task.state,
    }

    if task.state not in ('FAILURE', 'PENDING') and 'result' in task.info:
        response['result'] = task.info['result']
    
    if task.state == 'FAILURE':
        response['status'] = "Some error occurred during processing"
    elif 'status' in task.info:
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

            task = process_video.apply_async((inp_file_name, lang, res_format))

        else:
            vid_inp_file = request.files['vid_inp_file']
            session['original_filename'] = vid_inp_file.filename.split('.')[0]
            file_ext = vid_inp_file.filename.split('.')[-1]
            if file_ext=='mp3' and res_format == 'mp4':
                flash(u'Invalid result format', 'error')
                return redirect(request.url)
            inp_file_name = "{}.{}".format(str(session['uid']), file_ext)
            vid_inp_file.save(os.path.join(app.config['UPLOAD_FOLDER'], inp_file_name))

            if file_ext == 'mp4':
                task = process_video.apply_async((inp_file_name, lang, res_format))
            else:
                task = process_audio.apply_async((inp_file_name, lang))
            
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


