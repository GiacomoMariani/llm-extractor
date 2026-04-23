def chunk_text(text: str, chunk_size: int = 120, overlap: int = 30) -> list[str]:
    words = text.split()

    if not words:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    step = max(1, chunk_size - overlap)
    chunks: list[str] = []

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            continue

        chunks.append(" ".join(chunk_words))

        if start + chunk_size >= len(words):
            break

    return chunks