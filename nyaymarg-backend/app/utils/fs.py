import os
from pathlib import Path
from app.config import settings

def ensure_runtime_dirs():
    artefacts = Path(settings.MODEL_ARTEFACTS_DIR)
    uploads = Path(settings.UPLOAD_DIR)

    artefacts.mkdir(parents=True, exist_ok=True)
    uploads.mkdir(parents=True, exist_ok=True)

    return artefacts, uploads
