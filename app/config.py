import os

class Config:
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 1024)) * 1024 * 1024