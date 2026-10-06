import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    page_number: int | None
    chunk_index: int
    token_count: int


def chunk_pages(pages, tokenizer, size: int, overlap: int) -> list[Chunk]:
    """Token windows cut at source character offsets, retaining original wording."""
    chunks = []
    for page, text in pages:
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        offsets = encoded["offset_mapping"]
        if not offsets:
            continue
        start = 0
        while start < len(offsets):
            end = min(start + size, len(offsets))
            if end < len(offsets):
                left, right = offsets[start][0], offsets[end - 1][1]
                boundaries = list(re.finditer(r"\n\s*\n|[.!?](?:\s+|$)", text[left:right]))
                # Avoid fragments: prefer a boundary in the final quarter of the window.
                if boundaries:
                    cut = left + boundaries[-1].end()
                    candidates = [i + 1 for i in range(start, end) if offsets[i][1] <= cut]
                    if candidates and candidates[-1] - start >= max(overlap + 1, int(size * .75)):
                        end = candidates[-1]
            content = text[offsets[start][0]:offsets[end - 1][1]].strip()
            if content:
                count = len(tokenizer(content, add_special_tokens=False)["input_ids"])
                # Retokenizing a boundary can change token count; trim until within budget.
                while count > size and end > start + 1:
                    end -= 1
                    content = text[offsets[start][0]:offsets[end - 1][1]].strip()
                    count = len(tokenizer(content, add_special_tokens=False)["input_ids"])
                chunks.append(Chunk(content, page, len(chunks), count))
            if end == len(offsets):
                break
            start = max(start + 1, end - overlap)
    return chunks
