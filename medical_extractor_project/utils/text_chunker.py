# utils/text_chunker.py

def split_text_into_chunks(text: str, max_tokens_per_chunk: int = 4000, model_name: str = "gpt-4o") -> list:
    """
    Split text into chunks based on token limit.
    Returns a list of text chunks.
    """
    import tiktoken
    encoding = tiktoken.encoding_for_model(model_name)

    words = text.split()
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        word_tokens = len(encoding.encode(word + " "))
        if current_tokens + word_tokens > max_tokens_per_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_tokens = 0
        current_chunk.append(word)
        current_tokens += word_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
