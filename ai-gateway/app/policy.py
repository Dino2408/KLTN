from .config import AI_CONFIDENCE_THRESHOLD
from .schemas import Decision

# Deliberately small allowlist for the MVP.
APPROVED_AUTOMATION = {"PB-BRUTEFORCE-BLOCK-IP"}

def apply_policy(decision: Decision) -> bool:
    if decision.confidence < AI_CONFIDENCE_THRESHOLD:
        decision.requires_approval = True
        return False
    if decision.playbook not in APPROVED_AUTOMATION:
        decision.requires_approval = True
        return False
    if decision.severity == "critical":
        decision.requires_approval = True
        return False
    if decision.action != "block_source_ip":
        decision.requires_approval = True
        return False

    decision.requires_approval = False
    return True
