"""Upload the approved NovaFiber PDFs to the running local app."""
import json
import argparse
from getpass import getpass
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Administrator email")
    args = parser.parse_args()
    registry = json.loads((ROOT / "knowledge_base/document_registry.json").read_text(encoding="utf-8"))
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=300, trust_env=False) as client:
        login = client.post("/api/auth/login", json={"email": args.email, "password": getpass("Admin password: ")})
        login.raise_for_status()
        if login.json()["role"] != "admin":
            raise SystemExit("An administrator account is required.")
        client.headers["X-CSRF-Token"] = client.cookies.get("csrf_token")
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
