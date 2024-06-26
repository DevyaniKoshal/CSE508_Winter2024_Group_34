from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import requests
import socket


from spellchecker import SpellChecker
import re
import PyPDF2

data_folder = "/raid/home/arya20498/ir/flask/data"


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_words(text):
    words = re.findall(r'\b\w+\b', text.lower())  # Extract words and convert to lowercase
    return set(words)  # Use a set to avoid duplicates

def add_words_to_spellchecker(words):
    spell = SpellChecker()
    spell.word_frequency.load_words(words)
    return spell
def update_spellchecker_with_pdf(pdf_path):
    text=""
    for filename in os.listdir(data_folder):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(data_folder, filename)
            text = extract_text_from_pdf(pdf_path)
    words = extract_words(text)
    spell_checker = add_words_to_spellchecker(words)
    print("spellchecker updated")
    return spell_checker



app = Flask(__name__)
app.secret_key = os.urandom(24)

# Assuming '/raid/home/arya20498/ir/flask/upload' is your intended upload directory
os.makedirs(data_folder, exist_ok=True)


app.config['UPLOAD_FOLDER'] = data_folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit for files
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    # spell_checker = update_spellchecker_with_pdf(data_folder)
    spell_checker = SpellChecker()
    if 'messages' not in session:
        session['messages'] = []

    if request.method == 'POST':
        if 'query' in request.form:
            query = request.form['query']
            corrected_query_words = [spell_checker.correction(word) for word in query.split()]
            query = ' '.join(corrected_query_words)
            print(f'Corrected query: {query}')
            session['messages'].append({'user': True, 'content': query})
            session.modified = True
            response, similar_queries = send_query_to_server(query).split("$$")
            # reponse, sim = response
            sim_queries = ' '.join(similar_queries.split(":")[1:])
            sim_queries = sim_queries.split("?")[:-1]
            print(f"similar queries: {sim_queries}")
            session['messages'].append({'user': False, 'content': response})
            session.modified = True
            return render_template('index.html', messages=session['messages'], similar_queries=sim_queries)

        if 'url' in request.form:
            url = request.form.get('url')
            filename = request.form.get('filename', 'file.pdf')
            if url:
                filename = download_file_from_google_drive(url, filename)
                if filename:
                    query = "$file$added$"
                    response = send_query_to_server(query)
                    if response == "success":
                        flash(f"Downloaded {filename} successfully")
                        # spell_checker = update_spellchecker_with_pdf(data_folder)
                    else:
                        flash("failed")
                else:
                    flash("Failed to download the file.")
                return redirect(url_for('index'))

    return render_template('index.html', messages=session.get('messages', []), similar_queries=[])

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        flash('File uploaded successfully')
    else:
        flash('Invalid file type')
    return redirect(url_for('index'))

def download_file_from_google_drive(url, filename):
    file_id = get_google_drive_file_id(url)
    if not file_id:
        return None

    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    except requests.exceptions.RequestException as e:
        print(e)
        return None

def get_google_drive_file_id(url):
    """ Extract the file ID from a Google Drive URL """
    import re
    match = re.search(r'/d/(.*?)/', url)
    return match.group(1) if match else None

def send_query_to_server(query):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 6970))

    try:
        # Prepare the query data with a fixed-length header
        query_bytes = query.encode()
        header = len(query_bytes).to_bytes(4, byteorder='big')
        data = header + query_bytes

        # Send the data to the server
        client_socket.sendall(data)

        # Receive the response from the server
        response_data = b''
        header = client_socket.recv(4)
        expected_length = int.from_bytes(header, byteorder='big')
        received_length = 0
        while received_length < expected_length:
            packet = client_socket.recv(1024)
            response_data += packet
            received_length += len(packet)

        response = response_data.decode()
        print(f"response: {response}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"
    finally:
        client_socket.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
