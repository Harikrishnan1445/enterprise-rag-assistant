from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text(file_path: str, file_type: str) -> str:
    path = Path(file_path)

    if file_type == "txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if file_type == "pdf":
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if file_type == "docx":
        doc = DocxDocument(str(path))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)

    raise ValueError(f"Unsupported file type: {file_type}")