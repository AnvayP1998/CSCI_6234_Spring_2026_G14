import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings


class StorageService:

    def __init__(self):
        self.base_path = Path(settings.STORAGE_DIR)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file: UploadFile) -> str:
        """
        Saves uploaded file to storage directory.
        Returns relative file path.
        """
        file_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix

        stored_filename = f"{file_id}{extension}"
        file_path = self.base_path / stored_filename

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return str(file_path)