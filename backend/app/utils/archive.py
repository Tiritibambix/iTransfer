import os
import zipfile
from typing import List, Dict
from werkzeug.datastructures import FileStorage

def create_zip_archive(files: List[FileStorage], upload_dir: str) -> Dict:
    """
    Crée une archive ZIP à partir d'une liste de fichiers
    
    Args:
        files: Liste des fichiers à archiver
        upload_dir: Répertoire de destination
        
    Returns:
        Dict contenant le chemin de l'archive et la liste des fichiers
    """
    import uuid
    archive_id = str(uuid.uuid4())
    archive_name = f"archive_{archive_id}.zip"
    archive_path = os.path.join(upload_dir, archive_name)
    
    file_list = []
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            # Sauvegarder le fichier temporairement
            temp_path = os.path.join(upload_dir, file.filename)
            file.save(temp_path)
            
            # Ajouter à l'archive
            zipf.write(temp_path, file.filename)
            
            # Collecter les informations
            file_info = zipf.getinfo(file.filename)
            file_list.append({
                'path': file.filename,
                'size': file_info.file_size
            })
            
            # Nettoyer le fichier temporaire
            os.remove(temp_path)
    
    return {
        'archive_path': archive_path,
        'archive_name': archive_name,
        'files': file_list
    }
