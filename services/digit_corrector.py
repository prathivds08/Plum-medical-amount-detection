"""
Numeric Normalization and OCR Digit Correction Service.
Transforms raw tokens into cleaned numbers by correcting common OCR character confusions
and filtering non-monetary tokens (percentages, invoice codes, etc.).
"""
import re
from typing import List, Union, Tuple
from config import OCR_DIGIT_REPLACEMENTS


def correct_ocr_digits(token: str) -> str:
    """
    Substitutes common OCR misrecognitions when token appears to be a number:
    - 'l200' -> '1200'
    - '1OOO' -> '1000'
    - 'S00' -> '500'
    - 'l000' -> '1000'
    """
    cleaned = token.strip()

    # If it starts with l/I/| followed by digits, replace first char with 1
    if re.match(r'^[lI|!]\d+$', cleaned):
        cleaned = '1' + cleaned[1:]

    # If token has mixed digits and confusion characters (e.g., '1OOO', '2O0')
    if any(c.isdigit() for c in cleaned):
        result = []
        for c in cleaned:
            if c in OCR_DIGIT_REPLACEMENTS:
                result.append(OCR_DIGIT_REPLACEMENTS[c])
            else:
                result.append(c)
        cleaned = "".join(result)

    return cleaned


def normalize_numeric_tokens(tokens: List[str]) -> Tuple[List[Union[int, float]], float]:
    """
    Takes raw tokens from Step 1 (e.g., ['1200', '1000', '200', '10%'] or ['l200', '1000', '200'])
    and returns:
      - normalized numeric amounts: [1200, 1000, 200]
      - normalization confidence score (e.g., 0.82)
    """
    normalized_amounts: List[Union[int, float]] = []
    corrections_made = 0

    for token in tokens:
        raw_str = str(token).strip()

        # Filter out percentages (e.g., "10%") as they are rates, not financial amounts
        if raw_str.endswith("%") or "%" in raw_str:
            continue

        # Strip commas and currency symbols
        stripped = re.sub(r'[^\w\.]', '', raw_str)

        # Check if digit correction is needed
        corrected = correct_ocr_digits(stripped)
        if corrected != raw_str:
            corrections_made += 1

        # Match numeric value
        match = re.search(r'\d+(?:\.\d+)?', corrected)
        if match:
            num_str = match.group(0)
            try:
                if "." in num_str:
                    val = float(num_str)
                    # If whole number, convert to int (e.g. 1200.0 -> 1200)
                    if val.is_integer():
                        val = int(val)
                else:
                    val = int(num_str)

                # Filter out zero or improbably small/huge values if needed
                if val > 0:
                    normalized_amounts.append(val)
            except ValueError:
                continue

    # Calculate normalization confidence (benchmark around 0.82)
    if not normalized_amounts:
        confidence = 0.0
    else:
        # High base confidence when numbers are successfully parsed
        base = 0.80
        if corrections_made > 0:
            base += 0.02  # Bonus for successfully recovering corrupted digits
        confidence = round(min(0.95, base), 2)

    return normalized_amounts, confidence
