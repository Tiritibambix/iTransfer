from app import app, db
from app.routes import router

app = app

class FileUpload(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False)
    encrypted_data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

app.register_blueprint(router)

if __name__ == '__main__':
    app.run(debug=True)
