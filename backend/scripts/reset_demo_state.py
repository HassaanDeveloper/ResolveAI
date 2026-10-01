"""
Reset ResolveAI demo state.

Clears the workflow state that blocks re-running the console demo scenarios:
  * idempotency ledger rows (operations) for refund-/cancel- operation ids
  * refunds rows for the demo orders
  * resolutions rows and the approvals that reference them

This is required to clear the stale ledger state that permanently blocks order
10482: a cached "failed" operations row plus the refund row that a previous
attempt already wrote.

By default this runs as a DRY RUN and only prints what it would delete.
Pass --confirm to actually delete.

Usage:
    python scripts/reset_demo_state.py
    python scripts/reset_demo_state.py --confirm
    python scripts/reset_demo_state.py --confirm --orders 10482
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.database import get_supabase_client  # noqa: E402

# The orders used by the /console demo scenarios plus the primary seeded orders.
DEFAULT_DEMO_ORDERS = [
    "10482",  # Low-Value Refund  /  Cancel Shipped Order
    "10521",  # High-Value Refund
    "10356",  # Out-of-Policy Refund
    "10287",
    "10612",
]


def collect_state(client, order_numbers):
    """Gather every row that would be deleted, without deleting anything."""
    state = {"operations": [], "refunds": [], "resolutions": [], "approval_requests": []}

    ops = client.table("operations").select("operation_id, operation_type, status").execute()
    state["operations"] = [
        o for o in (ops.data or [])
        if any(f"order-{num}-" in o["operation_id"] or f"order-{num}" == o["operation_id"] for num in order_numbers)
    ]

    refunds = client.table("refunds").select("id, order_id, operation_id, amount, status").execute()
    order_uuids = set()
    for num in order_numbers:
        found = client.table("orders").select("id").eq("order_number", num).execute()
        for row in (found.data or []):
            order_uuids.add(row["id"])
    # Only refunds belonging to the demo orders are in scope.
    state["refunds"] = [r for r in (refunds.data or []) if r.get("order_id") in order_uuids]

    resolutions = client.table("resolutions").select("id, request_id, order_number, status").execute()
    state["resolutions"] = [r for r in (resolutions.data or []) if r.get("order_number") in order_numbers]

    resolution_ids = [r["id"] for r in state["resolutions"]]
    if resolution_ids:
        approvals = client.table("approval_requests").select("id, resolution_id, action_type, status").execute()
        state["approval_requests"] = [a for a in (approvals.data or []) if a.get("resolution_id") in set(resolution_ids)]

    return state


def report(state, order_numbers, applying):
    verb = "DELETE" if applying else "WOULD DELETE"
    print("=" * 78)
    print(f"Reset demo state for orders: {', '.join(order_numbers)}")
    print(f"Mode: {'APPLYING (--confirm)' if applying else 'DRY RUN - no changes will be made'}")
    print("=" * 78)

    ops = state["operations"]
    print(f"\n{verb} {len(ops)} row(s) from 'operations' (idempotency ledger):")
    for o in ops:
        print(f"    - {o['operation_id']}  [{o['status']}]")

    refunds = state["refunds"]
    print(f"\n{verb} {len(refunds)} row(s) from 'refunds':")
    for r in refunds:
        print(f"    - {r['id']}  operation_id={r.get('operation_id')}  amount={r.get('amount')}  status={r.get('status')}")

    res = state["resolutions"]
    print(f"\n{verb} {len(res)} row(s) from 'resolutions':")
    for r in res:
        print(f"    - {r['id']}  order={r.get('order_number')}  status={r.get('status')}")

    appr = state["approval_requests"]
    print(f"\n{verb} {len(appr)} row(s) from 'approval_requests':")
    for a in appr:
        print(f"    - {a['id']}  action={a.get('action_type')}  status={a.get('status')}")

    print(f"\nTOTAL: {len(ops) + len(refunds) + len(res) + len(appr)} row(s)")


def apply_deletions(client, state, order_numbers):
    deleted = {}

    ops = state["operations"]
    deleted["operations"] = len(ops)
    for o in ops:
        client.table("operations").delete().eq("operation_id", o["operation_id"]).execute()

    refunds = state["refunds"]
    deleted["refunds"] = len(refunds)
    for r in refunds:
        client.table("refunds").delete().eq("id", r["id"]).execute()

    res = state["resolutions"]
    deleted["resolutions"] = len(res)
    for r in res:
        client.table("resolutions").delete().eq("id", r["id"]).execute()

    appr = state["approval_requests"]
    deleted["approval_requests"] = len(appr)
    for a in appr:
        client.table("approval_requests").delete().eq("id", a["id"]).execute()

    print("\n" + "=" * 78)
    print("DELETED (actual row counts)")
    print("=" * 78)
    for table, count in deleted.items():
        print(f"    {table:<12} {count}")
    print(f"    {'TOTAL':<12} {sum(deleted.values())}")


def main():
    parser = argparse.ArgumentParser(description="Reset ResolveAI demo state")
    parser.add_argument("--confirm", action="store_true",
                        help="Actually delete rows. Without this flag the script only reports.")
    parser.add_argument("--orders", nargs="*", default=None,
                        help=f"Order numbers to reset (default: {' '.join(DEFAULT_DEMO_ORDERS)})")
    args = parser.parse_args()

    order_numbers = args.orders or DEFAULT_DEMO_ORDERS
    client = get_supabase_client()

    state = collect_state(client, order_numbers)
    report(state, order_numbers, applying=False)

    if not args.confirm:
        print("\nDry run complete. Re-run with --confirm to delete these rows.")
        return 0

    print("\n" + "-" * 78)
    print("Applying deletions...")
    print("-" * 78)
    apply_deletions(client, state, order_numbers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
