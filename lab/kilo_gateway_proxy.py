#!/usr/bin/env python3
"""Legacy relay reference.

The active workflow now uses the fixed-destination socat relay directly inside
the isolated egress container. This file remains as a human-readable record
of the old implementation boundary and is not executed by the workflow.
"""

DESTINATION = ("api.kilo.ai", 443)

if __name__ == "__main__":
    raise SystemExit(
        "The active Kilo relay is provisioned by .github/workflows/kilo-wakeup.yml."
    )
