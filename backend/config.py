import os

class Config:

    SECRET_KEY = "FraudDesk@2026SecureKey"

    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    UPLOAD_FOLDER = os.path.join(
        os.getcwd(),
        "uploads"
    )

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024