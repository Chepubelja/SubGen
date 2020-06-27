from flask import Flask, render_template,request, flash, redirect, session
import os

app = Flask(__name__)

UPLOAD_FOLDER = './files'
ALLOWED_EXTENSIONS = set(['mp4'])
#RESULT_FOLDER = './files'

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['RESULT_FOLDER'] = RESULT_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'vid_inp_file' not in request.files:
            flash('no input file')
            return redirect(request.url)

        vid_inp_file = request.files['vid_inp_file']

        if vid_inp_file and allowed_file(vid_inp_file.filename):
            #filename = secure_filename(vid_inp_file.filename)
            filename = vid_inp_file.filename
            vid_inp_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(request.url)

    else:
        return render_template("index.html")

if __name__ == "__main__":
    app.debug = True
    app.run()
