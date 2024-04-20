from flask import Flask, request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
import query_engine_setup
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit for files

query_engine = query_engine_setup.setup_query_engine()

@app.route('/', methods=['GET', 'POST'])


def index():
    # Initialize messages list if it doesn't exist in the session
    if 'messages' not in session:
        session['messages'] = []

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                response = f"Uploaded {filename} successfully."
                session['messages'].append({'user': False, 'content': response})
        elif 'query' in request.form:
            query = request.form['query']
            response = query_engine.query(query)
            session['messages'].append({'user': True, 'content': query})
            session['messages'].append({'user': False, 'content': response})

        session.modified = True  # Ensure changes are saved
        return render_template('index.html', messages=session['messages'])

    return render_template('index.html', messages=session.get('messages', []))

if __name__ == '__main__':
    app.run(debug=True)
