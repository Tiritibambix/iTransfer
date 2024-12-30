from flask import Flask, jsonify, request, send_from_directory
import os
import logging

app = Flask(__name__)

# Configurer les logs
logging.basicConfig(level=logging.INFO)

# Configurer le dossier d'uploads
UPLOAD_FOLDER = '/app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        if not file:
            raise ValueError("Aucun fichier envoyé")

        # Sauvegarder le fichier
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        logging.info(f"Fichier {file.filename} sauvegardé avec succès à {file_path}")
        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/uploads/<filename>')
def get_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/list-uploads', methods=['GET'])
def list_uploads():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return jsonify({"files": files})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
