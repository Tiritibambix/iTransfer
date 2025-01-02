from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Configurer CORS sans spécifier d'origine statique ici
CORS(app, supports_credentials=True)

@app.route('/')
def index():
    return jsonify({"message": "Bienvenue sur iTransfer API"})

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    # Récupérer l'URL du frontend dynamiquement pour chaque requête
    frontend_url = request.headers.get('Origin', 'http://localhost:3500')  # Si pas d'Origin, fallback à localhost:3500

    if request.method == 'OPTIONS':  # Gérer la pré-demande CORS
        response = jsonify({'message': 'CORS preflight success'})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    try:
        file = request.files.get('file')
        if not file:
            raise ValueError("Aucun fichier envoyé")

        # Sauvegarde du fichier
        upload_path = '/app/uploads/' + file.filename
        file.save(upload_path)

        response = jsonify({"message": f"Fichier {file.filename} reçu avec succès"})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 201
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", frontend_url)  # Ajouter le header CORS
        return response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Ecouter sur toutes les interfaces réseau