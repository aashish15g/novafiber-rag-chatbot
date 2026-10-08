"""Export NovaFiber PDFs and metadata using ReportLab and pypdf."""
import hashlib
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

ROOT = Path(__file__).resolve().parents[1] / "knowledge_base"
BLUE = colors.HexColor("#335cff")
INK = colors.HexColor("#15203d")
MUTED = colors.HexColor("#68738c")
STYLES = {
    "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=20, leading=25,
                            textColor=INK, spaceAfter=14),
    "metadata": ParagraphStyle("Metadata", fontName="Helvetica", fontSize=9, leading=13,
                               textColor=MUTED, spaceAfter=12),
    "heading": ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                              textColor=INK, spaceBefore=13, spaceAfter=6, keepWithNext=True),
    "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10.5, leading=15,
                           textColor=INK, spaceAfter=7, alignment=TA_LEFT),
}


def read_article(path):
    source = path.read_text(encoding="utf-8")
    title, *parts = source.split("\n## ")
    lines = title.strip().splitlines()
    metadata = dict(line.split(": ", 1) for line in lines[1:] if ": " in line)
    if len(parts) != 6:
        raise ValueError(f"Expected six sections in {path}")
    sections = []
    for part in parts:
        heading, body = part.split("\n", 1)
        sections.append((heading.strip(), body.strip()))
    required = {"Article ID", "Version", "Status", "Last reviewed", "Effective date",
                "Next review", "Category", "Topic", "Audience", "Classification", "Owner",
                "Applies to", "Related articles"}
    if missing := required - metadata.keys():
        raise ValueError(f"Missing metadata in {path}: {missing}")
    return lines[0].removeprefix("# "), metadata, sections


def render(path, title, meta, sections):
    article_id = meta["Article ID"]

    def decorate(canvas, doc):
        canvas.saveState()
        width, height = letter
        canvas.setFillColor(BLUE)
        canvas.roundRect(48, height - 48, 20, 20, 6, fill=1, stroke=0)
        canvas.setStrokeColor(colors.white)
        canvas.setLineWidth(1.5)
        canvas.lines([(53, height - 43, 53, height - 33),
                      (53, height - 33, 63, height - 43),
                      (63, height - 43, 63, height - 33)])
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(77, height - 41, "NovaFiber")
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(width - 48, height - 37,
                              f"KNOWLEDGE ARTICLE | {meta['Classification'].upper()}")
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(48, height - 66,
                          f"{article_id} | {title}")
        canvas.drawString(48, height - 79,
                          f"Version {meta['Version']} | {meta['Status']} | Effective {meta['Effective date']} | {meta['Classification']}")
        canvas.setStrokeColor(colors.HexColor("#e5e9f2"))
        canvas.line(48, height - 88, width - 48, height - 88)
        canvas.line(48, 43, width - 48, 43)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(48, 29, "Fictional company and policies | Training dataset | Not a real service agreement")
        canvas.drawRightString(width - 48, 29, f"{article_id} | Page {doc.page}")
        canvas.restoreState()

    story = [Paragraph(escape(title), STYLES["title"])]
    info = [f"<b>Article:</b> {escape(article_id)} | <b>Owner:</b> {escape(meta['Owner'])}",
            f"<b>Category:</b> {escape(meta['Category'])} | <b>Topic:</b> {escape(meta['Topic'])}",
            f"<b>Audience:</b> {escape(meta['Audience'])} | <b>Applies to:</b> {escape(meta['Applies to'])}",
            f"<b>Reviewed:</b> {escape(meta['Last reviewed'])} | <b>Next review:</b> {escape(meta['Next review'])}",
            f"<b>Related articles:</b> {escape(meta['Related articles'])}"]
    story.append(Paragraph("<br/>".join(info), STYLES["metadata"]))
    for index, (heading, body) in enumerate(sections):
        if index == 3:
            story.append(PageBreak())
        story.append(Paragraph(escape(heading), STYLES["heading"]))
        for paragraph in body.split("\n\n"):
            story.append(Paragraph(escape(paragraph).replace("\n", " "), STYLES["body"]))
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=48, rightMargin=48,
                           topMargin=104, bottomMargin=59, title=f"{article_id}: {title}",
                           author="NovaFiber - fictional broadband provider", pageCompression=1,
                           invariant=1)
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    reader = PdfReader(path)
    if len(reader.pages) != 2:
        raise ValueError(f"Layout must be two pages: {path} has {len(reader.pages)}")
    pages = [page.extract_text() or "" for page in reader.pages]
    for index, page in enumerate(pages):
        if article_id not in page or not page.strip():
            raise ValueError(f"Missing selectable text/provenance: {path}, page {index + 1}")
    section_pages = []
    for index, (heading, body) in enumerate(sections):
        page_index = 0 if index < 3 else 1
        normalized_page = re.sub(r"\s+", " ", pages[page_index])
        for expected in (heading, body):
            if re.sub(r"\s+", " ", expected) not in normalized_page:
                raise ValueError(f"Incomplete or misplaced content: {path}, section {heading}")
        section_pages.append({"heading": heading, "page": page_index + 1})
    return len(reader.pages), section_pages


def main():
    entries = []
    for source in sorted((ROOT / "sources").rglob("*.md")):
        title, meta, sections = read_article(source)
        access = source.relative_to(ROOT / "sources").parts[0]
        approved = access == "customer_approved"
        if approved != (meta["Audience"] == "customer_assistant"):
            raise ValueError(f"Audience/folder mismatch: {source}")
        if (meta["Classification"] == "internal") == approved:
            raise ValueError(f"Classification/folder mismatch: {source}")
        pdf = ROOT / "pdf" / source.relative_to(ROOT / "sources").with_suffix(".pdf")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        page_count, section_pages = render(pdf, title, meta, sections)
        entries.append({"article_id": meta["Article ID"], "title": title,
                        "category": meta["Category"], "topic": meta["Topic"],
                        "version": meta["Version"], "status": meta["Status"].lower(),
                        "audience": meta["Audience"], "classification": meta["Classification"],
                        "customer_chatbot_allowed": approved, "owner": meta["Owner"],
                        "applies_to": meta["Applies to"], "effective_date": meta["Effective date"],
                        "last_reviewed": meta["Last reviewed"], "next_review": meta["Next review"],
                        "related_article_ids": meta["Related articles"].split(", "),
                        "source_markdown": source.relative_to(ROOT).as_posix(),
                        "source_pdf": pdf.relative_to(ROOT).as_posix(), "source": pdf.name,
                        "file_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                        "page_count": page_count, "sections": section_pages})
    ids = {entry["article_id"] for entry in entries}
    if len(entries) != 20 or len(ids) != 20:
        raise ValueError("Expected exactly 20 unique articles")
    for entry in entries:
        if missing := set(entry["related_article_ids"]) - ids:
            raise ValueError(f"Unknown related IDs in {entry['article_id']}: {missing}")
    registry = {"schema_version": 1, "company": "NovaFiber", "synthetic": True,
                "locale": "en-US", "currency": "USD", "documents": entries}
    (ROOT / "document_registry.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    with ZipFile(ROOT / "NovaFiber_Customer_Documents.zip", "w", ZIP_DEFLATED) as archive:
        for entry in entries:
            if entry["customer_chatbot_allowed"]:
                pdf = ROOT / entry["source_pdf"]
                archive.write(pdf, Path(entry["source_pdf"]).relative_to("pdf/customer_approved").as_posix())
    print(f"Built {len(entries)} articles / {sum(e['page_count'] for e in entries)} pages.")
    print("Customer-approved: 16. Internal-only: 4. No ingestion performed.")


if __name__ == "__main__":
    main()
