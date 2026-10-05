#!/usr/bin/env python3
"""Clean up PROGRAM.json: deduplicate appended A24 history entries and normalize
generation counters back to +1 (the program was updated twice). Keeps all prior
history intact; never removes genuine prior evidence.
"""
import json
from pathlib import Path

PRG = Path("state/research/PROGRAM.json")
prog = json.load(open(PRG))

def dedupe(lst):
    seen, out = [], []
    for x in lst:
        if x not in seen:
            seen.append(x); out.append(x)
    return out

# Family-level histories
for fam in prog["evolution_families"]:
    for k in ("coverage_history", "independent_reproduction_history",
              "information_gain_history", "false_positive_history",
              "reasonable_effort_contribution", "results_history"):
        if isinstance(fam.get(k), list):
            fam[k] = dedupe(fam[k])

# Discovery notes dedupe
prog["discovery"]["uncertainty_notes"] = dedupe(prog["discovery"]["uncertainty_notes"])

# Normalize generations back to +1 over the original values
# Original gens (from pre-A24 bootstrap state): fam_27=8, fam_97=8, others=5, blocked_auth=3,
# non_viable=3, fam_41=3, fam_9=3, fam_29=3, redirect=3, chatbot=3
expected = {
    "fam_27_raw_error_discovery": 9, "fam_97_metrics_baseline": 9,
    "fam_23_memories_overexposure": 6, "fam_24_writegap": 6,
    "fam_5_security_question_enum": 6, "fam_7_captcha_leak": 6,
    "fam_6_put_tamper": 6,
    "fam_blocked_auth_sweep": 4, "fam_non_viable_500_monitor": 4,
    "fam_41_continue_code": 4, "fam_9_web3_nft": 4,
    "fam_29_extra_language": 4, "fam_redirect_ssrf_monitor": 4,
    "fam_chatbot_monitor": 4,
}
for fam in prog["evolution_families"]:
    fam["generation"] = expected[fam["family_id"]]

# Normalize surface uncertainty to list of strings (was str -> list)
for s in prog["surfaces"]:
    u = s.get("uncertainty")
    if isinstance(u, str):
        s["uncertainty"] = [u]

json.dump(prog, open(PRG, "w"), indent=1)
print("PROGRAM.json cleaned")
print("fam_27 gen:", next(f["generation"] for f in prog["evolution_families"] if f["family_id"]=="fam_27_raw_error_discovery"))
print("fam_27 coverage_history count:", len(next(f["coverage_history"] for f in prog["evolution_families"] if f["family_id"]=="fam_27_raw_error_discovery")))
print("uncertainty_notes count:", len(prog["discovery"]["uncertainty_notes"]))
