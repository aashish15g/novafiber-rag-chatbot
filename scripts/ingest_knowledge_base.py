"""Upload the approved NovaFiber PDFs to the running local app."""
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    registry = json.loads((ROOT / "knowledge_base/document_registry.json").read_text(encoding="utf-8"))
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=300, trust_env=False) as client:
        for entry in registry["documents"]:
            if not entry["customer_chatbot_allowed"]:
                continue
            path = ROOT / "knowledge_base" / entry["source_pdf"]
            with path.open("rb") as file:
                response = client.post("/api/documents", files={"file": (path.name, file, "application/pdf")})
            response.raise_for_status()
            result = response.json()
            label = "already indexed" if result["duplicate"] else "indexed"
            print(f"{entry['article_id']}: {label}, {result['document']['chunk_count']} chunks", flush=True)


if __name__ == "__main__":
    main()
