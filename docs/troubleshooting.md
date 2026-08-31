# Troubleshooting

## Raw rows arrive but target rows do not

Run the function directly, compare `getschema` with the target table, then query `.show ingestion failures` where `OriginatesFromUpdatePolicy == true`. With nontransactional policies, raw ingestion can succeed while a target fails.

## New field is absent from the typed table

This is expected until promotion. Query `ResidualTelemetry` and `ReviewTelemetryDrift()`.

## Known field becomes null

Inspect the raw dynamic value and `gettype()` result. Explicit cast functions return null for incompatible values; do not change a physical type without reviewing all producers and OneLake constraints.

## Zone counts differ from message counts

The relationship is one-to-many. Empty arrays create zero zone rows, while each populated element creates one row.

## Materialized view still contains duplicates

The configured lookback may be shorter than the actual duplicate-arrival interval. Measure arrivals before increasing it and benchmark the resulting materialization cost.
