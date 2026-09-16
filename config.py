"""
Application Configuration and Constants.
"""
import os
from typing import Dict, List

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Currency mappings
CURRENCY_MAP: Dict[str, str] = {
    "rs": "INR",
    "rs.": "INR",
    "inr": "INR",
    "₹": "INR",
    "rupees": "INR",
    "rupee": "INR",
    "$": "USD",
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "pound": "GBP",
    "a$": "AUD",
    "aud": "AUD",
    "c$": "CAD",
    "cad": "CAD",
}

# Default currency if none explicitly found
DEFAULT_CURRENCY = "INR"

# OCR Digit confusion mapping for amounts
# Handles common substitutions like 'l' -> '1', 'O' -> '0', 'o' -> '0', 'S' -> '5'
OCR_DIGIT_REPLACEMENTS = {
    'l': '1',
    'I': '1',
    '|': '1',
    '!': '1',
    'O': '0',
    'o': '0',
    'D': '0',
    'S': '5',
    's': '5',
    'B': '8',
    'Z': '2',
    'z': '2',
}

# Context keywords mapping for surrounding classification
CONTEXT_KEYWORDS = {
    "total_bill": [
        "total", "t0tal", "grand total", "bill amount", "total bill",
        "net payable", "invoice total", "gross", "bill value", "final total",
        "amount payable", "tot", "tota1"
    ],
    "paid": [
        "paid", "pald", "amount paid", "advance", "payment", "received",
        "amt paid", "paid amount", "cash paid", "card paid", "upi paid", "pa1d"
    ],
    "due": [
        "due", "balance due", "balance", "bal", "due amount", "outstanding",
        "remaining", "bal due", "pending"
    ],
    "discount": [
        "discount", "disc", "disct", "concession", "less", "rebate"
    ],
    "tax": [
        "tax", "gst", "cgst", "sgst", "vat"
    ]
}

# Minimum confidence threshold to avoid noisy false positives
MIN_TEXT_CONFIDENCE = 0.20
