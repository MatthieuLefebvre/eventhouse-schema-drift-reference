# Migration and Validation

## Sequence

1. Inventory the production landing schema, JSON mapping, payload paths, source types, retention, and consumers.
2. If OneLake availability is already enabled and its latency is acceptable, repoint existing Spark reads to the mirrored Delta table as a temporary export-path mitigation.
3. Deploy new target tables and run transform functions directly without policies.
4. Test normal, drifted, missing, malformed, type-conflicted, empty-array, and multi-array records.
5. Enable policies for one source type and shadow the existing pipeline.
6. Compare outputs, benchmark peak load, then expand source by source.
7. Retire Spark bulk reads, watermarks, drift buffers, and merge jobs only after acceptance.

## Equivalence Checks

- Raw and scalar-target counts by source type and time bucket.
- Distinct message IDs and anti-joins in both directions.
- Per-column null, minimum, maximum, and type-conversion failure rates.
- Residual-key preservation.
- Child rows per `(MessageId, ZoneId)` and empty-array behavior.
- Drift field paths, observed types, first/last seen, and sample values.
- Update-policy failure count and replay completeness.

## Benchmark Gates

Measure ingestion throughput, policy CPU, ingestion latency, target completeness, fan-out cost, and OneLake availability latency at representative peak concurrency. Each update-policy target adds ingestion work; capacity impact cannot be inferred from sample row counts.
