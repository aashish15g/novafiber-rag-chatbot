from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    page_number: int | None
    chunk_index: int
    token_count: int
    char_start: int
    char_end: int


def chunk_pages(pages, tokenizer, size, overlap):
    """Split pages into overlapping chunks, preserving text offsets."""
    chunks = []
    for page_number, text in pages:
        offsets = tokenizer(
            text, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        for start in range(0, len(offsets), size - overlap):
            end = min(start + size, len(offsets))
            left, right = offsets[start][0], offsets[end - 1][1]
            raw = text[left:right]
            left += len(raw) - len(raw.lstrip())
            right -= len(raw) - len(raw.rstrip())
            if left < right:
                chunks.append(Chunk(
                    text[left:right], page_number, len(chunks),
                    end - start, left, right))
            if end == len(offsets):
                break
    return chunks
