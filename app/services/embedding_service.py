from typing import List
import google.generativeai as genai
from app.config import get_settings
from app.utils.resilience import resilient_external_call
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


def _get_embedding_model():
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return 'models/text-embedding-004'


EXPECTED_EMBEDDING_DIMENSION = 768


@resilient_external_call("gemini", max_retries=3)
def encode_text(text: str) -> List[float]:
    model = _get_embedding_model()
    result = genai.embed_content(
        model=model,
        content=text,
        task_type="retrieval_document"
    )

    embedding = result.get('embedding')
    if not embedding:
        raise ValueError("Gemini returned no embedding")
    if len(embedding) != EXPECTED_EMBEDDING_DIMENSION:
        raise ValueError(f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIMENSION}, got {len(embedding)}")

    return embedding


def encode_batch(texts: List[str], max_workers: int = 5, timeout_per_item: float = 30.0) -> List[List[float]]:
    if not texts:
        return []

    results = [None] * len(texts)
    failed_count = 0

    def encode_with_index(index: int, text: str) -> tuple[int, List[float]]:
        embedding = encode_text(text)
        return (index, embedding)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(encode_with_index, i, text): i
            for i, text in enumerate(texts)
        }

        for future in as_completed(futures):
            original_index = futures[future]
            try:
                index, embedding = future.result(timeout=timeout_per_item)
                results[index] = embedding
            except TimeoutError:
                logger.error(f"Timeout encoding text at index {original_index}")
                failed_count += 1
            except Exception as e:
                logger.error(f"Failed to encode text at index {original_index}: {e}")
                failed_count += 1

    if failed_count == len(texts):
        raise ValueError(f"All {len(texts)} embedding requests failed")

    if failed_count > 0:
        logger.warning(f"{failed_count}/{len(texts)} embeddings failed")

    return results


def encode_catalog_item(name: str, description: str = "", category: str = "") -> List[float]:
    parts = [name]
    if category:
        parts.append(f"Category: {category}")
    if description:
        parts.append(description)

    combined_text = " | ".join(parts)
    return encode_text(combined_text)
