"""Enterprise Audit Trail & Immutable Log Export Module (T971)."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

def generate_audit_entry(
    user_id: str,
    action: str,  # 'LOGIN', 'MATCH_RUN', 'EXPORT_CSV', 'VIEW_PII', 'UPDATE_SETTINGS'
    resource_id: str,
    ip_address: str = "127.0.0.1",
    metadata: Optional[Dict[str, Any]] = None,
    previous_hash: str = "GENESIS_HASH"
) -> Dict[str, Any]:
    """Generate a tamper-evident audit log entry with SHA-256 integrity hash."""
    timestamp = datetime.now().isoformat()
    entry_payload = {
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "resource_id": resource_id,
        "ip_address": ip_address,
        "metadata": metadata or {},
        "previous_hash": previous_hash
    }
    raw_str = json.dumps(entry_payload, sort_keys=True)
    entry_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    entry_payload["hash"] = entry_hash
    return entry_payload

def verify_audit_chain_integrity(entries: List[Dict[str, Any]]) -> bool:
    """Verify integrity of a sequence of audit log entries."""
    if not entries:
        return True

    for i in range(len(entries)):
        current = entries[i]
        stored_hash = current.get("hash")
        
        # reconstruct payload
        payload = {k: v for k, v in current.items() if k != "hash"}
        calculated_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        
        if stored_hash != calculated_hash:
            return False

        if i > 0:
            if current.get("previous_hash") != entries[i - 1].get("hash"):
                return False

    return True

def export_enterprise_audit_report(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Export formatted audit report for enterprise compliance audits."""
    is_valid = verify_audit_chain_integrity(entries)
    return {
        "report_id": f"AUDIT-REP-{int(datetime.now().timestamp())}",
        "generated_at": datetime.now().isoformat(),
        "total_events_count": len(entries),
        "chain_integrity_verified": is_valid,
        "compliance_standard": "SOC2 Type II / ISO 27001 Ready",
        "events": entries
    }
