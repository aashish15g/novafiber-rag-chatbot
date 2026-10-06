import re
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


class TestTokenizer:
    """Deterministic token boundaries; production tokenizer is checked separately."""
    def __call__(self, text, **kwargs):
        matches = list(re.finditer(r"\S+", text))
        return {"input_ids": list(range(len(matches))), "offset_mapping": [m.span() for m in matches]}


class TestEmbeddings:
    dimension = 1024
    tokenizer = TestTokenizer()

    def load(self):
        pass

    def encode(self, texts, query=False):
        vectors = []
        for text in texts:
            words = text.lower()
            vector = [0.0] * 1024
            vector[0] = 1.0 if "return" in words else 0.0
            vector[1] = 1.0 if "ship" in words else 0.0
            vector[2] = .1
            vectors.append(vector)
        return vectors


class TestGenerator:
    calls = 0

    def generate(self, question, passages):
        self.calls += 1
        return f"According to the policy: {passages[0]['text']} [S1]", ["S1"]

    def close(self):
        pass


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, data_dir=tmp_path, max_upload_mb=1)


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings, TestEmbeddings(), TestGenerator())) as client:
        deadline = time.monotonic() + 5
        while not client.app.state.rag.ready:
            assert time.monotonic() < deadline
            time.sleep(.01)
        yield client


def policy_pdf(texts):
    """Generate a minimal valid multi-page PDF with a standard text font."""
    objects = [b"", b""]
    page_ids = []
    for text in texts:
        page_id = len(objects) + 1
        page_ids.append(page_id)
        stream_id = page_id + 1
        font_id = page_id + 2
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {stream_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>".encode())
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode()
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = f"<< /Type /Pages /Count {len(page_ids)} /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] >>".encode()
    data = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    data += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    data += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return data
