# Schema Evolution Runbook

## Operating Principle

New fields do not pause ingestion. They remain in `ResidualTelemetry` and produce append-only rows in `TelemetryDriftObservations`. Promotion is a reviewed metadata change.

## Review

1. Run `ReviewTelemetryDrift()` and identify the source type and path.
2. Query raw records across enough time and producers to inspect null rate, observed Kusto types, malformed values, cardinality, and semantic ownership.
3. Decide whether the field belongs in a physical column, remains dynamic, or requires a child table.
4. Record the approved target type, owner, backfill interval, and rollback decision.

## Promote

1. Add the column with `.alter-merge table`.
2. Revise the stored function to cast the field explicitly and remove it from the residual known-key list.
3. Ensure function output type and physical order match the target. Added columns appear at the end of the table schema.
4. Run the function over a bounded recent extent and compare `getschema` with `.show table ... schema as json`.
5. Monitor new ingestion and update-policy failures.

See `kql/07-promotion-backfill.kql` for the complete demo.

## Backfill

Kusto extents are immutable. A `.set-or-append` replay creates a newer complete version; it does not update the original row. Therefore:

- Use a latest-record materialized view/query when multiple versions per message are acceptable.
- Otherwise, build and validate a replacement table, then cut consumers over.
- Bound every replay by event or ingestion time and tag its extents.
- Record completed intervals externally or in a control table before rerunning.

## Failure Handling

With `IsTransactional:false`, raw data remains available when a target policy fails. Check `.show ingestion failures`, repair the function, select the affected raw interval using failure activity/time details, and replay only that interval into the target.
