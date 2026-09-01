# Presentation Notes

Use the detailed [presenter demo script](../docs/demo-script.md) for the live commands and expected results.

## 1. Handling schema drift in Eventhouse

Start with the problem, not a product comparison. JSON producers change over time, while reports and APIs need a dependable contract. This pattern is useful regardless of how the customer's current transformations are implemented.

## 2. Schema drift is more than a new field

Give one quick example for each kind of drift. Added fields are the easiest case. Type changes and missing fields are often more dangerous because the table still looks valid while values become null or misleading.

## 3. Flexible input, stable output

Explain the tension. Producers cannot coordinate every release with every report owner, but consumers cannot rewrite queries for every release. The solution is not to choose one side; it is to place a controlled boundary between them.

## 4. The five principles

Take time on this slide. Raw storage makes mistakes recoverable. Typed tables protect consumers. Residual JSON prevents data loss. Separate detection lets known processing continue. Reviewed promotion prevents accidental schema growth.

## 5. How the pieces fit together

Connect each principle to one Eventhouse object. Several update policies can read the same raw rows because each writes an independent target. Their execution order is not part of the design.

## 6. A new field arrives

Read the four telemetry values aloud. The concrete problem is that `serviceCountdownHours: 120` arrived before the target contract was changed. Keep returning to this exact value through promotion.

## 7. First, keep the whole payload

Point to `SourceType=controller` and `SchemaVersion=2` as physical columns. Then point to `120` inside `RawRecord`: `DropMappedFields` preserves the new value without adding a landing-table column.

## 8. Then write the fields we know

Read the resulting row. The approved values are typed columns; the exact new key/value pair is in `ResidualTelemetry`. Existing queries still receive the same schema.

## 9. Update policies do the routine work

Show the fan-out from one raw row to a typed row and drift evidence. Explain the deliberate `IsTransactional:false` availability tradeoff and required replay monitoring.

## 10. The new field goes onto the review list

Read the resulting observation: controller, `serviceCountdownHours`, `long`, and sample `120`. Connect each output to `bag_keys`, `mv-expand`, `set_has_element`, and `gettype`.

## 11. Arrays are handled as rows

Use the two fixture rows to make `mv-expand` tangible. The parent has two zones, so the child table has two rows with IDs 1 and 2. The next fixture's empty array creates no row.

## 12. Promotion is a normal code change

Contrast the exact before and after values. `120` moves from residual JSON to the typed `ServiceCountdownHours` column only after review. Appended replay versions require explicit consumer semantics.

## 13. An alert starts the conversation

Do not alert once per observation. Use a time window and evidence threshold appropriate to production volume. The payload must contain enough context to triage and should create or update one ticket per source and field.

## 14. Who looks at the ticket?

Walk across the ownership chain. Operations checks health, the source owner confirms intent, the domain owner defines meaning, engineering profiles and implements, and consumer/change owners approve. Small teams may combine roles, but detection itself never grants approval.

## 15. What the on-call engineer sees

The query pack supplies seven Real-Time Dashboard tiles. Separate operational failure from governance drift: a raw-to-target gap is high urgency, while a healthy residual field enters normal review.

## 16. Not every field becomes a column

Promotion is only one valid outcome. Sparse or unstable fields may remain dynamic; accidental or unsafe fields require a source fix or quarantine. Record every decision to prevent repeated tickets without hiding the residual data.

## 17. Where this can simplify an existing design

Ask how the customer handles parsing and drift today. Spark export is one scenario, not a prerequisite. Keep any external processing that provides real value; move only the routine work that is simpler and cheaper near ingestion.

## 18. A sensible way to start

Recommend a one-source shadow test. Compare cost, latency, completeness, replay behavior, array growth, and duplicates before changing the existing production path.
