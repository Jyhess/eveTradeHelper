"""
Test utilities
"""

import json
from pathlib import Path

# Path to tests directory
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


def save_reference(key: str, data):
    """
    Saves data as reference for tests

    Args:
        key: Reference name (filename without extension)
        data: Data to save (will be converted to JSON)
    """
    REFERENCE_DIR.mkdir(exist_ok=True)
    ref_file = REFERENCE_DIR / f"{key}.json"

    with open(ref_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def load_reference(key: str):
    """
    Loads a reference for comparison

    Args:
        key: Reference name (filename without extension)

    Returns:
        Reference data or None if not found
    """
    ref_file = REFERENCE_DIR / f"{key}.json"

    if not ref_file.exists():
        return None

    with open(ref_file, encoding="utf-8") as f:
        return json.load(f)


def normalize_for_comparison(data):
    """
    Normalizes data for comparison (removes non-important variations)

    Args:
        data: Data to normalize

    Returns:
        Normalized data
    """
    if isinstance(data, dict):
        # Sort keys and normalize values
        return {k: normalize_for_comparison(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        # Normalize each element and sort if possible
        normalized = [normalize_for_comparison(item) for item in data]
        # Try to sort if all elements are dicts with a common key
        if normalized and all(isinstance(item, dict) for item in normalized):
            if all("name" in item for item in normalized):
                normalized.sort(key=lambda x: x.get("name", ""))
            elif all("region_id" in item for item in normalized):
                normalized.sort(key=lambda x: x.get("region_id", 0))
        return normalized
    else:
        return data
