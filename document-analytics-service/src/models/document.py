from datetime import datetime
from src.models.user import db

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    content_text = db.Column(db.Text)
    classification = db.Column(db.String(100))
    classification_confidence = db.Column(db.Float)
    author = db.Column(db.String(255))
    creation_date = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'content_text': self.content_text,
            'classification': self.classification,
            'classification_confidence': self.classification_confidence,
            'author': self.author,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }

class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(500), nullable=False)
    results_count = db.Column(db.Integer, nullable=False)
    search_time = db.Column(db.Float, nullable=False)  # in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'results_count': self.results_count,
            'search_time': self.search_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

