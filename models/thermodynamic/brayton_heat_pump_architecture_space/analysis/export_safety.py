"""Output-safety helpers for Layer 4 analysis exports.

The physics engine keeps a full diagnostic ledger for every attempted case.
Analysis CSVs are stricter: performance quantities are exported only for valid
cases so out-of-envelope diagnostics cannot masquerade as evidence.
"""

from models.thermodynamic.brayton_heat_pump_architecture_space.core.physics_engine import ModelStatus


PERFORMANCE_FIELDS = {
    "t_sink_c",
    "t_sink_k",
    "eta_effective",
    "cop_hp",
    "q_total_out_w",
    "hp_useful_heat_w",
    "waste_heat_recovered_w",
    "total_useful_heat_out_w",
    "eta_sys",
    "layer4_hp_only_multiplier",
    "layer4_total_multiplier",
    "layer2_reversible_multiplier",
    "layer4_hp_only_fraction_of_layer2",
    "layer4_total_fraction_of_layer2",
    "pct_change_low",
    "pct_change_high",
}


def status_value(audit):
    status = audit.get("status")
    return status.value if isinstance(status, ModelStatus) else str(status)


def is_valid(audit):
    return audit.get("status") == ModelStatus.VALID


def status_msg(audit):
    return audit.get("status_msg", "")


def safe_value(audit, value):
    """Return a performance value only when the audit is valid."""
    return value if is_valid(audit) else None


def safe_metric_row(audit, values):
    """Build a row with validity metadata and nulled non-valid performance."""
    row = {
        "status": status_value(audit),
        "is_valid": is_valid(audit),
        "status_msg": status_msg(audit),
    }
    for key, value in values.items():
        row[key] = value if key not in PERFORMANCE_FIELDS else safe_value(audit, value)
    return row


def require_valid(audit, context):
    if not is_valid(audit):
        raise RuntimeError(f"{context} did not produce a valid audit: {status_msg(audit)}")
