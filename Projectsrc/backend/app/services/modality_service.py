from pathlib import Path

DOCUMENT_EXT = {".pdf", ".doc", ".docx", ".txt"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi"}

def detect_modality(filename: str) -> str:
    ext = Path(filename).suffix.lower()

    if ext in DOCUMENT_EXT:
        return "document"
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in VIDEO_EXT:
        return "video"

    # default fallback
    return "document"