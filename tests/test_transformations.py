import re
import pytest

# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

COUNTRY_MAP = {
    "USA": "US", "UNITED STATES": "US", "US": "US",
    "CAN": "CA", "CANADA": "CA", "CA": "CA",
    "GBR": "GB", "UNITED KINGDOM": "GB", "GB": "GB",
    "DEU": "DE", "GERMANY": "DE", "DE": "DE",
    "IND": "IN", "INDIA": "IN", "IN": "IN"
}

def standardize_country(raw_country: str) -> str:
    """Normalizes raw input strings to ISO-2 country codes."""
    if not raw_country:
        return "XX"
    return COUNTRY_MAP.get(raw_country.strip().upper(), "XX")

def sanitize_email(raw_email: str) -> tuple[str, bool]:
    """Validates email syntax, trims whitespace, and marks invalid formats."""
    if not raw_email:
        return "invalid_user@system.local", False
    cleaned = raw_email.strip().lower()
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if re.match(pattern, cleaned):
        return cleaned, True
    return "invalid_user@system.local", False

def sanitize_usage_count(raw_count) -> int:
    """Removes commas and currency symbols, enforcing non-negative integers."""
    if raw_count is None:
        return 0
    clean_val = re.sub(r"[\$,]", "", str(raw_count)).strip()
    try:
        val = int(clean_val)
        return max(val, 0)
    except ValueError:
        return 0


# ============================================================================
# UNIT TESTS (PYTEST)
# ============================================================================

def test_country_standardization():
    assert standardize_country("USA") == "US"
    assert standardize_country("United States") == "US"
    assert standardize_country("Germany") == "DE"
    assert standardize_country(None) == "XX"
    assert standardize_country("InvalidCountry") == "XX"

def test_email_sanitization():
    valid, is_ok = sanitize_email("  Alex.Rivera@Enterprise.Com ")
    assert valid == "alex.rivera@enterprise.com"
    assert is_ok is True

    fallback, is_bad = sanitize_email("corrupted_email_without_domain")
    assert fallback == "invalid_user@system.local"
    assert is_bad is False

def test_usage_count_sanitization():
    assert sanitize_usage_count("$45,000") == 45000
    assert sanitize_usage_count("-100") == 0
    assert sanitize_usage_count(None) == 0
    assert sanitize_usage_count("invalid_string") == 0