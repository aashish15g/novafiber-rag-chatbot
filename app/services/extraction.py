import re

from pypdf import PdfReader


class DocumentError(ValueError):
    pass


def normalize(text):
    # Keep this consistent with the page text used by existing citations.
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[^\S\n]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract(path):
    """Read PDF or TXT content as numbered pages."""
    try:
        if path.suffix.lower() == ".txt":
            pages = [(None, normalize(path.read_text(encoding="utf-8-sig")))]
        else:
            reader = PdfReader(path)
            pages = [(index + 1, normalize(page.extract_text() or ""))
                     for index, page in enumerate(reader.pages)]
    except Exception as exc:
        raise DocumentError("Could not read this file. Use a text-based PDF or UTF-8 TXT.") from exc

    pages = [(number, text) for number, text in pages if text]
    if not pages:
        raise DocumentError("The document contains no readable text.")
    return pages
