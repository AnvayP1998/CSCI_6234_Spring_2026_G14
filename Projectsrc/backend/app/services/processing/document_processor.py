import fitz  # pymupdf


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file using pymupdf."""
    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages).strip()


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()


def extract_text(file_path: str) -> str:
    """Dispatch to correct extractor based on extension."""
    lower = file_path.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    if lower.endswith(".txt"):
        return extract_text_from_txt(file_path)
    # .doc/.docx — stub for now
    return f"[Text extraction not yet supported for: {file_path}]"
