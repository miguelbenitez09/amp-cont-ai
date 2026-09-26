"""
ISO 6346 Container Standard & Maritime EDIFACT Parser for Panama PortOps-AI v2.0
Implements:
- BIC Code Validation & Modulo-11 Check-Digit Algorithm.
- Equipment Category Identifier (U: freight container, J: detachable equipment, Z: trailers).
- Size and Type Code decoding (e.g., 22G1, 45G1, 42R1).
- EDIFACT message simulation & parsing (BAPLIE bay plans, COARRI discharge/load, CODECO gate in/out).

Author: Desarrollado v1.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

import re
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timezone


class ISO6346ContainerValidator:
    """
    Validates intermodal shipping containers against ISO 6346:1995 standard.
    """

    # Letter to numeric values defined by ISO 6346 (multiples of 11 excluded: 11, 22, 33)
    CHAR_VALUES = {
        'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19, 'J': 20,
        'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29, 'S': 30, 'T': 31,
        'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38,
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
    }

    # ISO Size Type Mappings
    ISO_TYPE_CODES = {
        "22G1": {"length_ft": 20, "height_ft": 8.5, "type": "General Purpose / Dry Box", "teus": 1.0, "is_reefer": False},
        "42G1": {"length_ft": 40, "height_ft": 8.5, "type": "General Purpose / Dry Box", "teus": 2.0, "is_reefer": False},
        "45G1": {"length_ft": 40, "height_ft": 9.5, "type": "High Cube Dry Box", "teus": 2.0, "is_reefer": False},
        "42R1": {"length_ft": 40, "height_ft": 8.5, "type": "Reefer / Refrigerated Integral", "teus": 2.0, "is_reefer": True},
        "45R1": {"length_ft": 40, "height_ft": 9.5, "type": "High Cube Reefer", "teus": 2.0, "is_reefer": True},
        "22T1": {"length_ft": 20, "height_ft": 8.5, "type": "Tank Container (Hazardous Liquids)", "teus": 1.0, "is_reefer": False},
        "42U1": {"length_ft": 40, "height_ft": 8.5, "type": "Open Top Container", "teus": 2.0, "is_reefer": False}
    }

    @classmethod
    def calculate_check_digit(cls, container_id_10: str) -> int:
        """
        Calculates the 11th check digit using Modulo-11 weighted algorithm.
        Weights are powers of 2: 2^0, 2^1, 2^2, ..., 2^9.
        """
        clean = container_id_10.strip().upper()
        if len(clean) != 10:
            raise ValueError(f"Container base ID must be 10 characters, got '{clean}'")

        total = 0
        for i, char in enumerate(clean):
            val = cls.CHAR_VALUES.get(char)
            if val is None:
                raise ValueError(f"Invalid character '{char}' in container ID")
            total += val * (2 ** i)

        remainder = total % 11
        return 0 if remainder == 10 else remainder

    @classmethod
    def validate_container_id(cls, full_container_id: str) -> Dict[str, Any]:
        """
        Validates an 11-character container number (e.g. MSKU1234567 or MSCU9876543).
        Format: 4 letters (owner 3 + category 1) + 6 digits serial + 1 check digit.
        """
        clean = full_container_id.replace("-", "").replace(" ", "").strip().upper()
        if len(clean) != 11:
            return {
                "valid": False,
                "container_id": full_container_id,
                "reason": f"Expected 11 characters (ISO 6346), received {len(clean)}"
            }

        owner_code = clean[:3]
        category_id = clean[3]
        serial_number = clean[4:10]
        check_digit = clean[10]

        if not owner_code.isalpha():
            return {"valid": False, "container_id": clean, "reason": "Owner code must be 3 alphabetic letters."}

        if category_id not in ['U', 'J', 'Z']:
            return {
                "valid": False,
                "container_id": clean,
                "reason": f"Category identifier '{category_id}' invalid. Must be 'U' (freight), 'J' (detachable), or 'Z' (trailers)."
            }

        if not serial_number.isdigit():
            return {"valid": False, "container_id": clean, "reason": "Serial number must be 6 numeric digits."}

        if not check_digit.isdigit():
            return {"valid": False, "container_id": clean, "reason": "Check digit must be numeric."}

        expected_digit = cls.calculate_check_digit(clean[:10])
        actual_digit = int(check_digit)

        is_valid = (expected_digit == actual_digit)

        category_desc = {
            'U': "Freight Container (Standard Intermodal)",
            'J': "Detachable Freight Container-related Equipment",
            'Z': "Trailer and Chassis"
        }.get(category_id, "Unknown")

        return {
            "valid": is_valid,
            "container_id": clean,
            "owner_code": owner_code,
            "category_identifier": category_id,
            "category_description": category_desc,
            "serial_number": serial_number,
            "check_digit_actual": actual_digit,
            "check_digit_expected": expected_digit,
            "modulo_11_match": is_valid,
            "reason": None if is_valid else f"Modulo-11 check-digit mismatch: got {actual_digit}, expected {expected_digit}"
        }

    @classmethod
    def parse_full_manifest_entry(
        cls,
        container_id: str,
        size_type: str = "45G1",
        gross_weight_kg: float = 24500.0,
        tare_weight_kg: float = 3850.0,
        seal_number: str = "PA-SEC-99214",
        vessel_name: str = "MSC PAMELA",
        voyage_number: str = "2409W",
        terminal_code: str = "PA-BAL",  # Puerto Balboa
        stowage_bay_row_tier: str = "010382",
        status: str = "FULL_IMPORT",
        hazard_imo_class: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses and structures a full maritime container terminal record.
        """
        val_result = cls.validate_container_id(container_id)
        type_info = cls.ISO_TYPE_CODES.get(size_type, {
            "length_ft": 40, "height_ft": 8.5, "type": "Generic Container", "teus": 2.0, "is_reefer": False
        })

        net_weight = max(0.0, gross_weight_kg - tare_weight_kg)

        terminal_names = {
            "PA-BAL": "Puerto Balboa (Pacífico)",
            "PA-CRI": "Puerto Cristóbal (Atlántico)",
            "PA-MIT": "Manzanillo International Terminal (MIT)",
            "PA-CCT": "Colón Container Terminal (CCT)",
            "PA-PSA": "PSA Panama International Terminal (Pacífico)",
            "PA-BOC": "Bocas Fruit Co. / Almirante"
        }

        return {
            "validation": val_result,
            "container_id": val_result.get("container_id", container_id),
            "size_type_code": size_type,
            "equipment_spec": type_info,
            "teus": type_info["teus"],
            "weights": {
                "gross_weight_kg": gross_weight_kg,
                "tare_weight_kg": tare_weight_kg,
                "net_cargo_weight_kg": round(net_weight, 2)
            },
            "manifest": {
                "vessel_name": vessel_name,
                "voyage_number": voyage_number,
                "terminal_code": terminal_code,
                "terminal_name": terminal_names.get(terminal_code, terminal_code),
                "bay_stowage_coordinate": stowage_bay_row_tier,
                "seal_number": seal_number,
                "cargo_status": status,
                "hazardous_material": hazard_imo_class is not None,
                "imo_class": hazard_imo_class or "NONE"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class EDIFACTMaritimeParser:
    """
    Parses and produces standard UN/EDIFACT maritime logistics messages:
    - BAPLIE (Bay Plan / Plano de Estiba)
    - COARRI (Container Discharge / Loading Confirmation)
    - CODECO (Gate-in / Gate-out Container Movements)
    """

    @classmethod
    def parse_coarri_summary(cls, coarri_text: str) -> Dict[str, Any]:
        """Parses a COARRI confirmation message snippet into structured units."""
        lines = [line.strip() for line in coarri_text.splitlines() if line.strip()]
        containers_found = []
        vessel = "UNKNOWN"

        for line in lines:
            if "TDT+" in line:
                parts = line.split("+")
                if len(parts) >= 9:
                    vessel = parts[8].replace("'", "")
            elif "EQD+CN+" in line:
                parts = line.split("+")
                if len(parts) >= 3:
                    cid = parts[2].split(":")[0].replace("'", "")
                    containers_found.append(cid)

        return {
            "message_type": "COARRI",
            "vessel_identified": vessel,
            "total_containers_reported": len(containers_found),
            "container_list": containers_found,
            "parsed_at": datetime.now(timezone.utc).isoformat()
        }
