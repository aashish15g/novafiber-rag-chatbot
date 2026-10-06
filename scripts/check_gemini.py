"""Check provider access with a harmless prompt, without printing credentials."""
import re
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from google import genai
from google.genai import types


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Check another model without changing .env")
    parser.add_argument("--policy-check", action="store_true", help="Check structured citations using a synthetic policy")
    args = parser.parse_args()
    settings = Settings()
    if not settings.gemini_api_key.strip():
        print("No Gemini key is configured.")
        return 1
    client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(timeout=20000))
    try:
        models = list(client.models.list())
        available = [m.name for m in models if "generateContent" in (m.supported_actions or [])]
        print("Available text generation models:", ", ".join(available))
        model = args.model or settings.gemini_model
        if args.policy_check:
            from app.services.generation import GenerationService
            service = GenerationService(settings.gemini_api_key, model,
                                        settings.gemini_fallback_model if not args.model else "")
            try:
                answer, ids = service.generate("What is the return window?", [{
                    "source_id": "S1", "filename": "synthetic-policy.txt", "page_number": None,
                    "text": "Unopened products can be returned within 30 days of delivery."}])
                if ids != ["S1"] or "30" not in answer:
                    raise RuntimeError("The synthetic policy citation check did not pass.")
                print("Policy generation and citation validation passed:", answer)
                return 0
            finally:
                service.close()
        response = client.models.generate_content(model=model, contents="Reply with the word OK.")
        print("Checked model:", model)
        print("Configured model answered:", bool(response.text))
        return 0
    except Exception as exc:
        print("Provider error class:", type(exc).__name__)
        print("Provider status:", getattr(exc, "code", None))
        message = str(getattr(exc, "message", str(exc))).replace(settings.gemini_api_key, "[REDACTED]")
        message = re.sub(r"AIza[\w-]+", "[REDACTED]", message)
        print("Provider message:", message[:1200])
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
