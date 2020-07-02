from flask import Flask, render_template, request, flash, redirect, session, send_from_directory, jsonify, url_for, send_file
import uuid
import os
from celery import Celery
import time
import shutil

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
def my_task(self, inp_file, out_file):
    time.sleep(10)
    shutil.copyfile(os.path.join(app.config['UPLOAD_FOLDER'], inp_file),
                    os.path.join(app.config['RESULT_FOLDER'], out_file))
    return {'result': out_file}

@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = my_task.AsyncResult(task_id)
    response = {
        'state': task.state,
    }
    if task.state not in ('FAILURE', 'PENDING') and 'result' in task.info:
        response['result'] = task.info['result']

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
            out_file_name = "{}-result.{}".format(str(session['uid']), file_ext)
            vid_inp_file.save(os.path.join(app.config['UPLOAD_FOLDER'], inp_file_name))

            task = my_task.apply_async((inp_file_name, out_file_name))
            return render_template('index.html', Location=url_for('taskstatus', task_id=task.id))
        else:
            flash('some error occurred')
            return redirect(request.url)
    else:
        return render_template("index.html")

@app.route('/return-files/<path:filename>')
def return_files(filename):
    try:
        return send_file(os.path.join(app.config['RESULT_FOLDER'], filename), as_attachment=True)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.debug = True
    app.run()


