"""
ISO 6346 Container Number Validation & Check Digit Calculator — PortOps Plugin
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import Dict, Any


LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19, 'J': 20,
    'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29, 'S': 30, 'T': 31,
    'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
}


def validate_iso_6346(container_id: str) -> Dict[str, Any]:
    """
    Validates a 11-character container number per ISO 6346 standard.
    Format: 4 letters (Owner + Equipment Identifier) + 6 serial digits + 1 check digit.
    """
    cleaned = container_id.strip().upper().replace("-", "").replace(" ", "")
    if len(cleaned) != 11:
        return {
            "valid": False,
            "container_id": container_id,
            "error": f"Invalid length {len(cleaned)} (must be 11 characters)."
        }

    owner_code = cleaned[:3]
    category = cleaned[3]
    serial = cleaned[4:10]
    provided_check = cleaned[10]

    if not owner_code.isalpha() or not category.isalpha() or not serial.isdigit() or not provided_check.isdigit():
        return {
            "valid": False,
            "container_id": container_id,
            "error": "Format must be 4 uppercase letters followed by 7 digits."
        }

    # Calculate check digit
    total = 0
    weights = [2**i for i in range(10)]
    prefix = cleaned[:10]
    for i, char in enumerate(prefix):
        val = LETTER_VALUES[char] if char in LETTER_VALUES else int(char)
        total += val * weights[i]

    calculated_check = (total % 11) % 10
    is_valid = (int(provided_check) == calculated_check)

    return {
        "valid": is_valid,
        "container_id": cleaned,
        "owner_code": owner_code,
        "category_identifier": category,
        "serial_number": serial,
        "check_digit_provided": int(provided_check),
        "check_digit_calculated": calculated_check,
        "category_meaning": "Freight Container (U)" if category == 'U' else ("Detachable Equipment (J)" if category == 'J' else "Trailer (Z)")
    }
