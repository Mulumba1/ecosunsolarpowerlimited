import os

SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@ecosunsolarpower.com")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "mysql+mysqlconnector://root@127.0.0.1/ecosunsolarpowerdb"
)



MAIL_SERVER = os.environ.get("MAIL_SERVER", "mail.ecosunsolarpower.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "False") == "True"
MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "True") == "True"
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")