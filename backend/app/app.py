from flask import Flask, jsonify, request
import logging

app = Flask(__name__)

# Configurer les logs
logging.basicConfig(level=logging.INFO)

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
        file.save(f"/uploads/{file.filename}")
        logging.info(f"Fichier {file.filename} sauvegardé avec succès")
        return jsonify({"message": f"Fichier {file.filename} reçu avec succès"}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'upload : {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
