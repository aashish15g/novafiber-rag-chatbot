import re
from pathlib import Path

from pypdf import PdfReader


class DocumentError(ValueError):
    pass


def normalize(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract(path: Path) -> list[tuple[int | None, str]]:
    if path.suffix.lower() == ".txt":
        try:
            text = normalize(path.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError as exc:
            raise DocumentError("TXT files must use UTF-8 encoding.") from exc
        if not text:
            raise DocumentError("The document contains no readable text.")
        return [(None, text)]
    try:
        with path.open("rb") as handle:
            if not handle.read(1024).lstrip().startswith(b"%PDF-"):
                raise DocumentError("The uploaded file is not a valid PDF.")
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise DocumentError("Encrypted PDFs are not supported. Upload an unencrypted copy.")
        pages = [(i + 1, normalize(page.extract_text() or "")) for i, page in enumerate(reader.pages)]
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("This PDF could not be read. It may be corrupt or unsupported.") from exc
    if not pages or not any(text for _, text in pages):
        raise DocumentError("This PDF has no readable text and may require OCR.")
    if any(not text for _, text in pages):
        raise DocumentError("One or more PDF pages have no extractable text. Upload a text-based copy or use OCR first.")
    return pages
