"""
app/ml/pipeline.py — NLP text preprocessing for NyayMarg.
"""
from __future__ import annotations

import re

# Legal stopwords — comprehensive list for Indian court text
_STOPWORDS: frozenset[str] = frozenset([
    "the", "and", "is", "in", "to", "of", "a", "for", "on", "with",
    "as", "by", "at", "an", "be", "this", "that", "which", "are", "was",
    "were", "been", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "not",
    "from", "or", "but", "if", "it", "its", "their", "they", "we",
    "he", "she", "his", "her", "our", "you", "your", "my", "me", "him",
    "us", "who", "whom", "whose", "what", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "so", "yet", "both", "either",
    "than", "too", "very", "just", "also", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "about",
    "against", "over", "under", "again", "then", "once", "here",
    "there", "same", "own", "only", "so", "because", "although", "though",
])


def clean_text(text: str) -> str:
    """
    Clean a single piece of legal text:
    1. Lowercase
    2. Remove all non-alpha chars
    3. Collapse whitespace
    4. Remove stopwords
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [w for w in text.split() if w not in _STOPWORDS and len(w) > 1]
    return " ".join(tokens)


def clean_batch(texts: list[str]) -> list[str]:
    """Clean a list of texts."""
    return [clean_text(t) for t in texts]
