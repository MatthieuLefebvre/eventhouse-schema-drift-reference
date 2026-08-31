# Limitations and Decisions

- `IsTransactional:false` protects raw ingestion but permits target gaps. Monitoring and replay are mandatory.
- Update-policy fan-out consumes ingestion-path CPU for every target.
- Automatic schema inference is intentionally absent. Promotion requires evidence and review.
- Existing-key type changes can cast to null. Inspect raw values and drift/type-quality queries.
- Nested objects remain dynamic unless explicit paths are promoted.
- Arrays are normalized into child rows; very large arrays can amplify ingestion volume.
- Drift observations are append-only and can repeat. Aggregate them for review.
- Historical backfill appends versions because extents are immutable.
- The optional one-hour deduplication lookback is a demo value only.
- Local validation cannot prove KQL execution. Run smoke tests in a disposable Fabric Eventhouse.
- No preview features are required.
