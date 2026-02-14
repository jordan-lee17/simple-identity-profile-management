from typing import Optional
from api.models import Person, NameRecord

PREFERRED_ORDER = ["preferred", "professional", "legal"]

def mask_name(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if len(v) == 1:
        return v + "*"
    return v[0] + "***"

def build_safe_person_label(person: Person) -> str:
    # Fetch name_records in the view
    records = list(person.name_records.all())

    def pick(type_: str) -> Optional[NameRecord]:
        for r in records:
            if r.type.lower() == type_.lower() and r.sensitivity_level != "high":
                return r
        return None

    chosen = None
    for t in PREFERRED_ORDER:
        chosen = pick(t)
        if chosen:
            break

    if not chosen:
        return f"Person {person.id}"

    # Show full name for low, masked for medium
    if chosen.sensitivity_level == "medium":
        shown = mask_name(chosen.value)
    else:
        shown = chosen.value

    return f"{shown} ({chosen.type})"