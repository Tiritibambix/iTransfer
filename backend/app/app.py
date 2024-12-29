from flask import Flask, jsonify, request
import logging
import os

app = Flask(__name__)

# Configurer les logs
logging.basicConfig(level=logging.INFO)

# Assurez-vous que le répertoire de téléchargement existe
UPLOAD_FOLDER = '/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        # Valider la présence d'un fichier
        if not file:
            raise ValueError("Aucun fichier envoyé")

        # Exemple de traitement (remplacer par logique métier réelle)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        logging.info(f"Fichier {file.filename} sauvegardé avec succès à {file_path}")
        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
