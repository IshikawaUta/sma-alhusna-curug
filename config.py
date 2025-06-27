import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci_rahasia_yang_kuat_dan_unik_untuk_aplikasi_anda'

    MONGO_URI = os.environ.get('MONGO_URI') or "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/?retryWrites=true&w=majority"
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME') or "school_website_db"

    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or "admin"
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or "password123"

    # --- Konfigurasi Flask-Mail ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'Flase'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # --- Konfigurasi Pagination ---
    POSTS_PER_PAGE = 3 # Jumlah postingan per halaman blog
