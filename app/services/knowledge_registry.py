import json

from app.config import ROOT
from app.services.extraction import DocumentError


class KnowledgeRegistry:
    """Look up NovaFiber article metadata by file hash."""
    def __init__(self):
        entries = json.loads((ROOT / "knowledge_base/document_registry.json").read_text(
            encoding="utf-8"))["documents"]
        self.by_hash = {entry["file_sha256"]: entry for entry in entries}

    def metadata(self, filename, digest):
        entry = self.by_hash.get(digest)
        if entry is None:
            return {"company": "NovaFiber", "title": filename, "customer_chatbot_allowed": True}
        if not entry["customer_chatbot_allowed"]:
            raise DocumentError("Internal articles are not part of the customer knowledge base.")
        return {"company": "NovaFiber", **{
            key: value for key, value in entry.items()
            if key not in {"file_sha256", "source_pdf", "source_markdown"}}}
