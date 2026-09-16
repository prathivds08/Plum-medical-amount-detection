"""
Context Classification Service.
Analyzes surrounding text and tokens to accurately label financial amounts
(e.g., 'total_bill', 'paid', 'due', 'discount', 'tax').
"""
import re
from typing import List, Dict, Any, Tuple, Union, Optional
from config import CONTEXT_KEYWORDS


def _fuzzy_keyword_match(text_snippet: str) -> Optional[str]:
    """
    Finds the closest semantic financial category for a surrounding text snippet.
    Handles OCR misspellings like 'T0tal', 'Pald', 'tot', 'bal', etc.
    """
    snippet_clean = text_snippet.lower().replace(":", " ").replace("|", " ").replace("=", " ")
    words = snippet_clean.split()

    # Direct match against configured keywords
    for category, keywords in CONTEXT_KEYWORDS.items():
        for kw in keywords:
            if kw in snippet_clean:
                return category

    # Fuzzy checks for common OCR typos
    for w in words:
        # Check for 'total' variations: t0tal, tota1, tota
        if re.match(r'^t[o0][t1]a?[l1]?$', w) or "tot" in w:
            return "total_bill"
        # Check for 'paid' variations: pald, pa1d, payed
        if re.match(r'^p[a@]?[l1i]d$', w) or "paid" in w:
            return "paid"
        # Check for 'due' variations: dwe, du, ba1
        if re.match(r'^d[u][e]?$', w) or "due" in w or "bal" in w:
            return "due"
        # Check for discount
        if "disc" in w:
            return "discount"

    return None


def classify_amounts_by_context(
    normalized_amounts: List[Union[int, float]],
    context_text: str
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Takes normalized amounts and original/extracted context text,
    and classifies each amount into categories: 'total_bill', 'paid', 'due', etc.

    Example input:
      normalized_amounts: [1200, 1000, 200]
      context_text: "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"
    Expected Output:
      [
        {"type": "total_bill", "value": 1200},
        {"type": "paid", "value": 1000},
        {"type": "due", "value": 200}
      ], confidence=0.80
    """
    if not normalized_amounts:
        return [], 0.0

    classified_items: List[Dict[str, Any]] = []
    text_lower = context_text.lower()

    # Split text into segments (by pipe, comma, newline, or semicolon)
    raw_segments = re.split(r'[|\n;]', context_text)
    clean_segments = [s.strip() for s in raw_segments if s.strip()]

    assigned_types = set()

    for amount in normalized_amounts:
        amount_str = str(amount)
        # Also form variants for OCR corruptions (e.g. for 1200, search for '1200', 'l200')
        variants = [amount_str]
        if amount_str.startswith("1"):
            variants.append("l" + amount_str[1:])
            variants.append("I" + amount_str[1:])

        best_category = None
        best_distance = float("inf")

        # First pass: search in segments
        for seg in clean_segments:
            seg_lower = seg.lower()
            for var in variants:
                # Use boundary check so '200' doesn't match '1200' or 'l200'
                if re.search(r'(?:^|[^\w])' + re.escape(var) + r'(?:[^\w]|$)', seg_lower):
                    cat = _fuzzy_keyword_match(seg)
                    if cat:
                        best_category = cat
                        break
            if best_category:
                break

        # Second pass: if segment search didn't label, look in character window before the number
        if not best_category:
            for var in variants:
                matches = list(re.finditer(r'(?:^|[^\w])(' + re.escape(var) + r')(?:[^\w]|$)', text_lower))
                if matches:
                    pos = matches[0].start(1)
                    start = max(0, pos - 25)
                    window = text_lower[start:pos]
                    cat = _fuzzy_keyword_match(window)
                    if cat:
                        best_category = cat
                        break

        # Third pass: Fallback heuristic based on relative magnitude & balance equation
        if not best_category:
            if amount == max(normalized_amounts) and "total_bill" not in assigned_types:
                best_category = "total_bill"
            elif "paid" not in assigned_types:
                best_category = "paid"
            elif "due" not in assigned_types:
                best_category = "due"
            else:
                best_category = "misc_amount"

        assigned_types.add(best_category)
        classified_items.append({
            "type": best_category,
            "value": amount
        })

    # Validate logical consistency for ordering and categories:
    # If we have total_bill, paid, due, ensure they align with arithmetic Total = Paid + Due
    total_item = next((item for item in classified_items if item["type"] == "total_bill"), None)
    paid_item = next((item for item in classified_items if item["type"] == "paid"), None)
    due_item = next((item for item in classified_items if item["type"] == "due"), None)

    # Calculate classification confidence score
    confidence = 0.80
    if total_item and paid_item and due_item:
        if total_item["value"] == paid_item["value"] + due_item["value"]:
            confidence = 0.85  # Math verification reinforces confidence
    
    return classified_items, confidence
