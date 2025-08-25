import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Pinecone settings
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT') or 'gcp-starter'
    PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME') or 'paris-18'

# Images folder path - use environment variable for GCP
IMAGES_FOLDER = os.getenv('IMAGES_FOLDER', '/Users/alex/Desktop/addresses-paris')

# GCP Configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'real-estate-images')