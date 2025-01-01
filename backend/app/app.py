from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Exemple d'authentification (à adapter selon tes besoins)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username')
    password = data.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return jsonify({"message": "Authenticated"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        upload_path = os.path.join('/app/uploads', file.filename)
        file.save(upload_path)
        return jsonify({"message": f"File {file.filename} uploaded successfully."}), 201
    return jsonify({"message": "No file uploaded."}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
