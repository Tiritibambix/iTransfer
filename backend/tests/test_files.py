import os
import pytest
from io import BytesIO
from app import create_app
from app.extensions import db
from app.models import FileUpload, ArchiveContent

@pytest.fixture
def app():
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def create_test_file(name="test.txt", content=b"test content"):
    return (BytesIO(content), name)

def test_upload_single_file(client):
    """Test l'upload d'un seul fichier"""
    file_content = b"Test file content"
    file = create_test_file("test.txt", file_content)
    
    data = {
        'files[]': (file[0], file[1]),
        'email': 'test@example.com'
    }
    
    response = client.post('/upload', 
                         data=data,
                         content_type='multipart/form-data')
    
    assert response.status_code == 201
    assert 'file_id' in response.json
    
    # Vérifier l'entrée en base de données
    file_upload = FileUpload.query.get(response.json['file_id'])
    assert file_upload is not None
    assert file_upload.filename == "test.txt"
    assert not file_upload.is_archive

def test_upload_multiple_files(client):
    """Test l'upload de plusieurs fichiers"""
    files = [
        create_test_file("file1.txt", b"content 1"),
        create_test_file("file2.txt", b"content 2")
    ]
    
    data = {
        'files[]': [(f[0], f[1]) for f in files],
        'email': 'test@example.com'
    }
    
    response = client.post('/upload',
                         data=data,
                         content_type='multipart/form-data')
    
    assert response.status_code == 201
    assert 'file_id' in response.json
    
    # Vérifier l'archive en base de données
    file_upload = FileUpload.query.get(response.json['file_id'])
    assert file_upload is not None
    assert file_upload.is_archive
    
    # Vérifier le contenu de l'archive
    contents = ArchiveContent.query.filter_by(
        file_upload_id=response.json['file_id']
    ).all()
    assert len(contents) == 2

def test_get_file_details(client):
    """Test la récupération des détails d'un fichier"""
    # Créer un fichier test en base
    file_id = "test-id-123"
    file_upload = FileUpload(
        id=file_id,
        filename="archive.zip",
        email="test@example.com",
        is_archive=True
    )
    db.session.add(file_upload)
    
    # Ajouter des fichiers à l'archive
    contents = [
        ArchiveContent(
            file_upload_id=file_id,
            file_path="file1.txt",
            file_size=100
        ),
        ArchiveContent(
            file_upload_id=file_id,
            file_path="file2.txt",
            file_size=200
        )
    ]
    for content in contents:
        db.session.add(content)
    
    db.session.commit()
    
    # Tester l'API
    response = client.get(f'/api/files/{file_id}')
    
    assert response.status_code == 200
    assert response.json['filename'] == "archive.zip"
    assert response.json['is_archive']
    assert len(response.json['contents']) == 2

def test_download_file(client):
    """Test le téléchargement d'un fichier"""
    # Créer un fichier test
    file_id = "test-id-123"
    filename = "test.txt"
    file_content = b"Test content"
    
    # Créer le fichier physique
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    with open(os.path.join(upload_folder, filename), 'wb') as f:
        f.write(file_content)
    
    # Créer l'entrée en base
    file_upload = FileUpload(
        id=file_id,
        filename=filename,
        email="test@example.com",
        is_archive=False
    )
    db.session.add(file_upload)
    db.session.commit()
    
    # Tester le téléchargement
    response = client.get(f'/download/{file_id}')
    
    assert response.status_code == 200
    assert response.data == file_content
    
    # Nettoyer
    os.remove(os.path.join(upload_folder, filename))
