from typing import List
from api.models import *

class AbacDecision:
    def __init__(self, allowed: List[NameRecord], denied_reason: str):
        self.allowed = allowed
        self.denied_reason = denied_reason

def evaluate_abac( 
    *,
    requester: Requester,
    context: str,
    name_records: List[NameRecord],
) -> AbacDecision:
    # Load context policy
    try:
        policy = ContextPolicy.objects.get(context_name=context)
    except ContextPolicy.DoesNotExist:
        return AbacDecision([], denied_reason="No policy for context")

    # Check requester role
    if requester.role.lower() != "admin" and requester.role.lower() != policy.required_role.lower():
        return AbacDecision([], denied_reason="Requester role not permitted for context")

    # Filter by allowed_name_types
    allowed_types = set(t.lower() for t in policy.allowed_name_types)

    allowed = []
    for record in name_records:
        if record.type.lower() not in allowed_types:
            continue

        # Sensitivity filtering
        if record.sensitivity_level == "high" and requester.role.lower() != "admin":
            allow_high = bool((policy.additional_rules or {}).get("allow_high", False))
            if not allow_high:
                continue

        allowed.append(record)

    if not allowed:
        return AbacDecision([], denied_reason="No fields allowed after policy filtering")

    return AbacDecision(allowed, denied_reason=None)
