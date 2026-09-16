"""
Provenance Tracking and Step 4 Response Assembly.
Extracts the exact text clause/snippet where each amount was found to establish
data lineage ('provenance') and performs mathematical consistency validation.
"""
import re
from typing import List, Dict, Any, Union, Tuple


def extract_provenance_source(amount: Union[int, float], context_text: str, label: str = "") -> str:
    """
    Finds the exact clause or text snippet around the amount.
    Returns format: "text: '<snippet>'"
    Example: "text: 'Total: INR 1200'"
    """
    amount_str = str(amount)
    
    # Potential representations in text (original digits or OCR variants like 'l200')
    search_terms = [amount_str]
    if amount_str.startswith("1"):
        search_terms.append("l" + amount_str[1:])
        search_terms.append("I" + amount_str[1:])

    # Split context by pipes, newlines, semicolons to isolate clauses
    clauses = re.split(r'[|\n;]', context_text)
    
    # Check clauses with word boundary
    candidates = []
    for c in clauses:
        clause_str = c.strip()
        for term in search_terms:
            if re.search(r'(?:^|[^\w])' + re.escape(term) + r'(?:[^\w]|$)', clause_str, re.IGNORECASE):
                candidates.append(clause_str)
                break

    if candidates:
        if label:
            # Pick candidate whose text best matches label
            clean_label = label.replace("_", " ").lower()
            for cand in candidates:
                if any(w in cand.lower() for w in clean_label.split()):
                    return f"text: '{cand}'"
        return f"text: '{candidates[0]}'"

    # If not isolated cleanly in a clause, search for window around the term
    for term in search_terms:
        matches = list(re.finditer(r'(?:^|[^\w])(' + re.escape(term) + r')(?:[^\w]|$)', context_text, re.IGNORECASE))
        if matches:
            idx = matches[0].start(1)
            start = max(0, idx - 15)
            end = min(len(context_text), idx + len(term) + 5)
            snippet = context_text[start:end].strip()
            return f"text: '{snippet}'"

    return f"text: '{amount_str}'"


def validate_financial_math(classified_amounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates arithmetic relationship between extracted amounts:
      Total Bill == Paid + Due
    Provides auditable AI chaining verification.
    """
    total = None
    paid = None
    due = None

    for item in classified_amounts:
        cat = item.get("type")
        val = item.get("value")
        if cat == "total_bill" and total is None:
            total = val
        elif cat == "paid" and paid is None:
            paid = val
        elif cat == "due" and due is None:
            due = val

    if total is not None and paid is not None and due is not None:
        is_balanced = (round(total, 2) == round(paid + due, 2))
        return {
            "is_balanced": is_balanced,
            "equation": f"{total} == {paid} + {due}",
            "discrepancy": round(total - (paid + due), 2) if not is_balanced else 0
        }

    return {
        "is_balanced": None,
        "equation": "Incomplete components for Total = Paid + Due check",
        "discrepancy": None
    }


def build_step4_final_output(
    classified_amounts: List[Dict[str, Any]],
    currency: str,
    context_text: str
) -> Dict[str, Any]:
    """
    Constructs the Step 4 final output payload strictly conforming to PDF spec:
    {
      "currency": "INR",
      "amounts": [
        {"type":"total_bill","value":1200,"source":"text: 'Total: INR 1200'"},
        {"type":"paid","value":1000,"source":"text: 'Paid: 1000'"},
        {"type":"due","value":200,"source":"text: 'Due: 200'"}
      ],
      "status":"ok"
    }
    """
    amounts_with_provenance = []

    for item in classified_amounts:
        amt_type = item["type"]
        val = item["value"]
        source_snippet = extract_provenance_source(val, context_text, label=amt_type)

        amounts_with_provenance.append({
            "type": amt_type,
            "value": val,
            "source": source_snippet
        })

    return {
        "currency": currency or "INR",
        "amounts": amounts_with_provenance,
        "status": "ok"
    }
