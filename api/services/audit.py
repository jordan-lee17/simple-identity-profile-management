import hashlib
from django.conf import settings

# Compute SHA-256 signature
def compute_audit_signature(*, payload: str, prev_signature: str | None) -> str:
    # For project use
    # Change to a dedicated signing key for prod
    secret = settings.SECRET_KEY  
    base = f"{secret}|{prev_signature or ''}|{payload}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def build_audit_payload(*, requester_id: int, person_id: int, context_used: str,
                        fields_returned: list, decision: str, denied_reason: str | None, timestamp_iso: str) -> str:
    fields = ",".join(sorted([str(x) for x in fields_returned]))
    denied = denied_reason or ""
    return f"{requester_id}|{person_id}|{context_used}|{fields}|{decision}|{denied}|{timestamp_iso}"

# Recompute signature and compare
def verify_audit_log_entry(log) -> bool:
    payload = build_audit_payload(
        requester_id=log.requester_id,
        person_id=log.person_id,
        context_used=log.context_used,
        fields_returned=log.fields_returned,
        decision=log.decision,
        denied_reason=log.denied_reason,
        timestamp_iso=log.timestamp.isoformat(),
    )
    expected = compute_audit_signature(payload=payload, prev_signature=log.prev_signature)
    return (log.signature == expected)
