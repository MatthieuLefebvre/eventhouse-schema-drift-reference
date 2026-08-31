# Presentation Notes

## 1. Schema drift without bulk export

Set expectations: this is a reusable implementation pattern, not an automatic-schema promise.

## 2. The customer problem

Explain that Kusto connector reads can use the export path. The concern is concurrent bulk transformation, not ordinary interactive querying.

## 3. Current data path

Watermarks, buffers, target-schema reads, and merge jobs are secondary complexity created after data leaves Eventhouse.

## 4. Stable-schema principle

The target contract never changes merely because an input key appears. Unknown data remains queryable in the residual bag.

## 5. Target architecture

Each target is an ordinary table. Policies run independently and execution order is not guaranteed or required.

## 6. Per-record processing

Casting failures generally produce nulls; retain raw data so compatibility decisions can be revised and replayed.

## 7. Arrays become child rows

Avoid runtime-generated columns. Confirm array amplification and identity semantics with the customer.

## 8. Drift review

Seeing a key once is insufficient evidence for physical promotion.

## 9. Promotion and backfill

Extents are immutable. Appended replay versions need a latest-record view or a replacement-table migration.

## 10. OneLake role

Mirrored Delta can be a useful transition, but it has adaptive batching and schema-operation constraints.

## 11. Production gates

Benchmark on representative payload size, rate, concurrency, array size, retention, and duplicates.

## 12. Recommended next steps

Start with one source type, retain rollback coverage, and expand only after completeness and capacity gates pass.
