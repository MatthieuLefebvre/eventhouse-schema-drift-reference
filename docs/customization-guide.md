# Customization Guide

The demo uses fixed names so it can run without templating. For a customer deployment, copy the modules and change the contract deliberately.

| Demo item | Customer decision |
|---|---|
| `RawTelemetry` | Existing landing table or a new raw table |
| Envelope columns | Exact names, casing, and Kusto types from the production mapping |
| `RawRecord.payload.telemetry` | Actual residual JSON path after `DropMappedFields` |
| Source types | Routing values present in production data |
| Known-key lists | Approved physical fields for each source type |
| Cast functions | Compatibility behavior for every known key |
| Zone row model | Array identity, maximum size, and empty-array behavior |
| Retention | Raw replay horizon and target retention requirements |
| Transactionality | Raw availability versus source/target atomicity |
| Deduplication | Stable key, duplicate-arrival window, and cardinality |

Before enabling a policy, run its function directly over a recent bounded extent and compare `getschema` with the target table. Update policies require column type and order to match the target.

Do not infer production types from one JSON sample. Profile multiple schema versions and malformed records, then make casts explicit.