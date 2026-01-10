"""Product enrichment using Gemini AI."""
import json
import logging
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import google.generativeai as genai

from app.config import get_settings
from app.utils.resilience import resilient_external_call

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """You are a product data enrichment assistant. Given a product name, provide accurate product information as structured data.

{context}

Extract the following:
1. Standardized Name
2. Description (1-2 sentences)
3. Category (Electronics, Furniture, Office Supplies, Software, Services, etc.)
4. Vendor/Manufacturer
5. Price in USD (null if unavailable)
6. Pricing Type: "one_time", "monthly", "yearly", "usage_based", or null
7. Product URL (official page)
8. SKU/Model number
9. Metadata (brand, specs, features)
10. Confidence: "high", "medium", or "low"

Return ONLY valid JSON:
{{
    "name": "string",
    "description": "string",
    "category": "string",
    "vendor": "string",
    "price": null or number,
    "pricing_type": "one_time" | "monthly" | "yearly" | "usage_based" | null,
    "product_url": "string or null",
    "sku": "string or null",
    "metadata": {{}},
    "confidence": "high" | "medium" | "low"
}}

Use null for unknown fields. Only include price if you find a clear USD value."""


def _get_gemini_client():
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


@resilient_external_call("gemini", max_retries=3)
def enrich_product(
    product_name: str,
    category: Optional[str] = None,
    additional_context: Optional[str] = None
) -> Dict:
    """Use Gemini AI to populate product fields from a product name."""
    settings = get_settings()

    context = f"Product name: {product_name}"
    if category:
        context += f"\nCategory: {category}"
    if additional_context:
        context += f"\nContext: {additional_context}"

    prompt = ENRICHMENT_PROMPT.format(context=context)

    try:
        model = _get_gemini_client()
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
        )

        result_text = response.text.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```json\n', 1)[-1]
            result_text = result_text.rsplit('```', 1)[0].strip()

        enriched_data = json.loads(result_text)

        for field in ['name', 'description', 'category', 'vendor', 'confidence']:
            if field not in enriched_data or not enriched_data[field]:
                raise ValueError(f"Missing required field: {field}")

        if 'metadata' not in enriched_data or not isinstance(enriched_data['metadata'], dict):
            enriched_data['metadata'] = {}

        return enriched_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response: {e}")
    except Exception as e:
        raise Exception(f"Product enrichment failed: {str(e)}")


def enrich_product_batch(
    product_names: List[str],
    max_workers: int = 5,
    timeout_per_item: float = 60.0
) -> List[Dict]:
    """Enrich multiple products in parallel. Deduplicates to save API calls."""
    if not product_names:
        return []

    results = [None] * len(product_names)

    # Deduplicate: map unique names to their indices
    unique_names: Dict[str, List[int]] = {}
    for i, name in enumerate(product_names):
        normalized = name.strip().lower()
        if normalized not in unique_names:
            unique_names[normalized] = []
        unique_names[normalized].append(i)

    unique_items = [
        (norm, product_names[indices[0]], indices)
        for norm, indices in unique_names.items()
    ]

    logger.info(f"Batch enrichment: {len(product_names)} items, {len(unique_items)} unique")

    def enrich_with_key(normalized: str, original_name: str) -> tuple[str, Dict]:
        return (normalized, enrich_product(original_name))

    def make_error_result(product_name: str, error_msg: str) -> Dict:
        return {
            "name": product_name,
            "description": "",
            "category": "",
            "vendor": "",
            "price": None,
            "pricing_type": None,
            "product_url": None,
            "sku": None,
            "metadata": {},
            "confidence": "low",
            "error": error_msg
        }

    enriched_cache: Dict[str, Dict] = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(enrich_with_key, norm, name): (norm, name)
            for norm, name, _ in unique_items
        }

        for future in as_completed(futures):
            normalized, original_name = futures[future]
            try:
                key, result = future.result(timeout=timeout_per_item)
                enriched_cache[key] = result
            except TimeoutError:
                logger.error(f"Timeout enriching '{original_name}'")
                enriched_cache[normalized] = make_error_result(original_name, "Enrichment timed out")
            except Exception as e:
                logger.error(f"Failed to enrich '{original_name}': {e}")
                enriched_cache[normalized] = make_error_result(original_name, str(e))

    for normalized, indices in unique_names.items():
        result = enriched_cache.get(normalized)
        if result:
            for idx in indices:
                results[idx] = result.copy()

    return results
