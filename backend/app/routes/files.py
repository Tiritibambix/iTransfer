import os
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from ..models import FileUpload, ArchiveContent
from ..extensions import db
from ..utils.archive import create_zip_archive
from ..utils.email import send_email
import uuid

bp = Blueprint('files', __name__)

@bp.route('/api/files/<file_id>', methods=['GET'])
def get_file_details(file_id):
    """Récupère les détails d'un fichier"""
    try:
        file_upload = FileUpload.query.get_or_404(file_id)
        
        response = {
            'filename': file_upload.filename,
            'is_archive': file_upload.is_archive,
            'created_at': file_upload.created_at.isoformat()
        }
        
        if file_upload.is_archive:
            contents = ArchiveContent.query.filter_by(file_upload_id=file_id).all()
            response['contents'] = [
                {'path': c.file_path, 'size': c.file_size}
                for c in contents
            ]
            
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des détails : {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/upload', methods=['POST'])
def upload_files():
    """Gère l'upload de fichiers multiples"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
            
        files = request.files.getlist('files[]')
        email = request.form.get('email')
        
        if not email:
            return jsonify({'error': 'Email requis'}), 400
            
        file_id = str(uuid.uuid4())
        
        # Si plusieurs fichiers, créer une archive
        if len(files) > 1:
            archive_info = create_zip_archive(files, current_app.config['UPLOAD_FOLDER'])
            
            # Créer l'entrée dans la base de données
            file_upload = FileUpload(
                id=file_id,
                filename=archive_info['archive_name'],
                email=email,
                is_archive=True
            )
            
            # Ajouter les détails du contenu
            for file_info in archive_info['files']:
                content = ArchiveContent(
                    file_upload_id=file_id,
                    file_path=file_info['path'],
                    file_size=file_info['size']
                )
                db.session.add(content)
                
        else:
            # Cas d'un seul fichier
            file = files[0]
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            file_upload = FileUpload(
                id=file_id,
                filename=filename,
                email=email,
                is_archive=False
            )
        
        # Sauvegarder en base de données
        db.session.add(file_upload)
        db.session.commit()
        
        # Envoyer l'email
        try:
            send_email(email, file_id, file_upload.filename)
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi de l'email : {str(e)}")
        
        return jsonify({
            'message': 'Upload réussi',
            'file_id': file_id
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'upload : {str(e)}")
        return jsonify({'error': str(e)}), 500
