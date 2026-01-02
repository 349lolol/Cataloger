"""
Product enrichment service using Gemini AI with search capabilities.
Automatically populates product fields (price, vendor, SKU, etc.) from a product name.
"""
import json
import google.generativeai as genai
from typing import Dict, Optional, List
from app.config import get_settings
from app.utils.resilience import resilient_external_call
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


def _get_gemini_client():
    """Get configured Gemini client."""
    settings = get_settings()
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


@resilient_external_call("gemini", max_retries=3)
def enrich_product(
    product_name: str,
    category: Optional[str] = None,
    additional_context: Optional[str] = None
) -> Dict:
    """
    Use Gemini AI with search to automatically populate product fields.

    This function uses Gemini Flash with Google Search grounding to find
    real-time product information and structure it for catalog ingestion.

    Args:
        product_name: Descriptive product name (e.g., "MacBook Pro 16 inch M3 Max")
        category: Optional category hint to improve search accuracy
        additional_context: Optional additional context for disambiguation

    Returns:
        Dictionary with enriched product fields:
        {
            "name": str,              # Cleaned/standardized product name
            "description": str,       # Generated product description
            "category": str,          # Inferred or confirmed category
            "vendor": str,            # Manufacturer/vendor name
            "price": float,           # Current price in USD (if found)
            "pricing_type": str,      # "one_time", "monthly", "yearly", "usage_based"
            "product_url": str,       # Official product page URL
            "sku": str,               # Product SKU or model number
            "metadata": dict,         # Additional attributes (brand, specs, etc.)
            "confidence": str         # "high", "medium", "low" based on search results
        }

    Example:
        result = enrich_product("MacBook Pro 16 inch M3 Max", category="Electronics")
        # Returns structured data with price, vendor (Apple), SKU, etc.
    """
    settings = get_settings()

    # Build enrichment prompt
    prompt_context = f"Product name: {product_name}"
    if category:
        prompt_context += f"\nCategory: {category}"
    if additional_context:
        prompt_context += f"\nAdditional context: {additional_context}"

    prompt = f"""You are a product data enrichment assistant. Given a product name, use your knowledge to provide accurate product information and return structured data.

{prompt_context}

Based on the product name, extract the following information:

1. **Standardized Name**: Clean, official product name
2. **Description**: 1-2 sentence product description highlighting key features
3. **Category**: Product category (Electronics, Furniture, Office Supplies, Software, Services, etc.)
4. **Vendor**: Manufacturer or primary vendor name
5. **Price**: Current price in USD (if available). Return null if not found or if pricing varies significantly.
6. **Pricing Type**: Classify as:
   - "one_time" for one-time purchases
   - "monthly" for monthly subscriptions
   - "yearly" for annual subscriptions
   - "usage_based" for metered/consumption pricing
7. **Product URL**: Link to official product page or primary vendor listing
8. **SKU**: Product SKU, model number, or product code
9. **Metadata**: Additional structured attributes like:
   - brand
   - specifications (screen size, RAM, storage, etc.)
   - warranty information
   - key features
10. **Confidence**: Rate your confidence in the data ("high", "medium", "low") based on:
    - Search result quality and consistency
    - Whether you found an official product page
    - Price availability and currency

Return ONLY a valid JSON object with this exact structure (no markdown, no code blocks):
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

If you cannot find reliable information for a field, use null. Be conservative with price data - only include if you find a clear, current USD price."""

    try:
        model = _get_gemini_client()

        # Use Gemini to generate product data
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,  # Low temperature for factual accuracy
                top_p=0.8,
                top_k=40,
                max_output_tokens=2048,
            )
        )

        # Parse JSON response
        result_text = response.text.strip()

        # Handle markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```json\n', 1)[-1]
            result_text = result_text.rsplit('```', 1)[0].strip()

        enriched_data = json.loads(result_text)

        # Validate required fields
        required_fields = ['name', 'description', 'category', 'vendor', 'confidence']
        for field in required_fields:
            if field not in enriched_data or not enriched_data[field]:
                raise ValueError(f"Missing or empty required field: {field}")

        # Ensure metadata exists
        if 'metadata' not in enriched_data or not isinstance(enriched_data['metadata'], dict):
            enriched_data['metadata'] = {}

        return enriched_data

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}. Response: {result_text[:200]}")
    except Exception as e:
        raise Exception(f"Product enrichment failed: {str(e)}")


def enrich_product_batch(
    product_names: List[str],
    max_workers: int = 5,
    timeout_per_item: float = 60.0
) -> List[Dict]:
    """
    Enrich multiple products in parallel using ThreadPoolExecutor.

    Uses concurrent processing to significantly improve performance.
    Example: 20 products @ 3s each = 12s total (vs 60s sequential)

    Args:
        product_names: List of product names to enrich
        max_workers: Maximum number of concurrent threads (default: 5)
        timeout_per_item: Timeout in seconds for each enrichment call (default: 60)

    Returns:
        List of enriched product data dictionaries (maintains input order).
        Failed items will have an "error" field and confidence="low".
    """
    if not product_names:
        return []

    results = [None] * len(product_names)  # Pre-allocate to maintain order

    def enrich_with_index(index: int, product_name: str) -> tuple[int, Dict]:
        """Enrich product and return with index for ordering."""
        result = enrich_product(product_name)
        return (index, result)

    def make_error_result(product_name: str, error_msg: str) -> Dict:
        """Create an error result dict for failed enrichments."""
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

    # Process in parallel with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(enrich_with_index, i, name): (i, name)
            for i, name in enumerate(product_names)
        }

        # Collect results as they complete with timeout
        for future in as_completed(futures):
            original_index, product_name = futures[future]
            try:
                index, result = future.result(timeout=timeout_per_item)
                results[index] = result
            except TimeoutError:
                logger.error(f"Timeout enriching product '{product_name}'")
                results[original_index] = make_error_result(product_name, "Enrichment timed out")
            except Exception as e:
                logger.error(f"Failed to enrich product '{product_name}': {e}")
                results[original_index] = make_error_result(product_name, str(e))

    return results
