import os
import subprocess
import tempfile

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            )
        # Downloads ~140 MB 'base' model on first use, cached afterwards
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def _transcribe(audio_path: str) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio_path, beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments)
    return text if text.strip() else "[No speech detected in audio]"


def extract_text_from_audio(file_path: str) -> str:
    return _transcribe(file_path)


def extract_text_from_video(file_path: str) -> str:
    """Extract audio track from video with ffmpeg, then transcribe with Whisper."""
    import shutil
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is not installed or not on PATH. "
            "Install ffmpeg to enable video transcription: https://ffmpeg.org/download.html"
        )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", file_path,
                "-ar", "16000",   # 16 kHz sample rate (Whisper requirement)
                "-ac", "1",       # mono
                "-vn",            # no video
                tmp_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed to extract audio from video.\n{result.stderr[-500:]}"
            )
        return _transcribe(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
