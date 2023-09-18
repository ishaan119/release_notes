import os

from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()


class Config:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///features.db'  # SQLite URI
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    # AWS S3 configuration
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    FLASK_ENV = os.getenv("FLASK_ENV")
    FLASK_PORT = 8000


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///features.db'
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    # AWS S3 configuration
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    FLASK_ENV = os.getenv("FLASK_ENV")
    FLASK_PORT = 80
