# Presentation Notes

Use the detailed [presenter demo script](../docs/demo-script.md) for the live commands and expected results.

## 1. Handling schema drift in Eventhouse

This is a worked example, not an automatic schema-management product. The aim is to keep routine telemetry shaping close to the data while leaving schema decisions with the team.

## 2. Where we started

Walk through the current path from left to right. The point is not that Spark is a poor tool; it is that we are exporting data to perform parsing and routing that Eventhouse can handle as it arrives.

## 3. The extra work adds up

There are two costs here. Export and Spark startup use capacity. The surrounding watermarks, buffers, and merge jobs also give the team more state to monitor and recover.

## 4. The revised data path

Point out the raw replay point, typed tables, child rows, and drift table. These are ordinary tables, so OneLake mirroring remains an option where another Fabric engine needs the data.

## 5. A new field arrives

Read the four telemetry values aloud. The concrete problem is that `serviceCountdownHours: 120` arrived before the target contract was changed. Keep returning to this exact value through promotion.

## 6. First, keep the whole payload

Point to `SourceType=controller` and `SchemaVersion=2` as physical columns. Then point to `120` inside `RawRecord`: `DropMappedFields` preserves the new value without adding a landing-table column.

## 7. Then write the fields we know

Read the resulting row. The approved values are typed columns; the exact new key/value pair is in `ResidualTelemetry`. Existing queries still receive the same schema.

## 8. Update policies do the routine work

Show the fan-out from one raw row to a typed row and drift evidence. Explain the deliberate `IsTransactional:false` availability tradeoff and required replay monitoring.

## 9. The new field goes onto the review list

Read the resulting observation: controller, `serviceCountdownHours`, `long`, and sample `120`. Connect each output to `bag_keys`, `mv-expand`, `set_has_element`, and `gettype`.

## 10. Arrays are handled as rows

Use the two fixture rows to make `mv-expand` tangible. The parent has two zones, so the child table has two rows with IDs 1 and 2. The next fixture's empty array creates no row.

## 11. Promotion is a normal code change

Contrast the exact before and after values. `120` moves from residual JSON to the typed `ServiceCountdownHours` column only after review. Appended replay versions require explicit consumer semantics.

## 12. An alert starts the conversation

Do not alert once per observation. Use a time window and evidence threshold appropriate to production volume. The payload must contain enough context to triage and should create or update one ticket per source and field.

## 13. Who looks at the ticket?

Walk across the ownership chain. Operations checks health, the source owner confirms intent, the domain owner defines meaning, engineering profiles and implements, and consumer/change owners approve. Small teams may combine roles, but detection itself never grants approval.

## 14. What the on-call engineer sees

The query pack supplies seven Real-Time Dashboard tiles. Separate operational failure from governance drift: a raw-to-target gap is high urgency, while a healthy residual field enters normal review.

## 15. Not every field becomes a column

Promotion is only one valid outcome. Sparse or unstable fields may remain dynamic; accidental or unsafe fields require a source fix or quarantine. Record every decision to prevent repeated tickets without hiding the residual data.

## 16. A sensible way to start

Recommend a one-source shadow test. Compare cost, latency, completeness, replay behavior, array growth, and duplicates before removing any existing Spark path.
