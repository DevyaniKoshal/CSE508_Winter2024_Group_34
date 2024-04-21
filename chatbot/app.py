import socket
import pickle
from flask import Flask, request, render_template, session, redirect, url_for
import os


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit for files

@app.route('/', methods=['GET', 'POST'])
def index():
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
            response = send_query_to_server(query)
            session['messages'].append({'user': True, 'content': query})
            session['messages'].append({'user': False, 'content': response})
            session.modified = True
            return render_template('index.html', messages=session['messages'])
    return render_template('index.html', messages=session.get('messages', []))

def send_query_to_server(query):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 6969))

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
    app.run(debug=True, host='0.0.0.0', port=5000)
