import re


def sanitize_input(text: str, max_len: int) -> str:
    """Basic sanitization: remove code fences/backticks, URLs, emails, excessive whitespace.
    Clamp to max_len.
    """
    if not text:
        return text
    cleaned = text
    cleaned = re.sub(r"```[\s\S]*?```", " ", cleaned)
    cleaned = cleaned.replace("`", " ")
    cleaned = re.sub(r"https?://\S+", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned 