# Presentation Notes

Use the detailed [presenter demo script](../docs/demo-script.md) for the live commands and expected results.

## 1. Move schema drift from Spark to Eventhouse

Set expectations: the goal is to prove a reusable KQL pattern, not promise automatic, ungoverned schema creation.

## 2. Start with today's Spark journey

Walk left to right. Eventhouse already owns the data, but the notebook exports it to infer and flatten it. Keep the discussion specific to recurring telemetry processing rather than criticizing Spark broadly.

## 3. Why the current loop is less efficient

Separate direct cost from operational complexity. Export and Spark startup consume resources; watermarks, buffers, and merges also create more failure and recovery states.

## 4. What the demo builds instead

Use the architecture to identify the raw replay point, typed tables, child rows, and drift evidence. Ordinary target tables can optionally be mirrored to OneLake.

## 5. Meet the message we will follow

Read the four telemetry values aloud. The concrete problem is that `serviceCountdownHours: 120` arrived before the target contract was changed. Keep returning to this exact value through promotion.

## 6. Step 1: raw mapping loses nothing

Point to `SourceType=controller` and `SchemaVersion=2` as physical columns. Then point to `120` inside `RawRecord`: `DropMappedFields` preserves the new value without adding a landing-table column.

## 7. Step 2: typed row stays predictable

Read the resulting row. The approved values are typed columns; the exact new key/value pair is in `ResidualTelemetry`. Existing queries still receive the same schema.

## 8. Step 3: policies process it automatically

Show the fan-out from one raw row to a typed row and drift evidence. Explain the deliberate `IsTransactional:false` availability tradeoff and required replay monitoring.

## 9. Step 4: drift becomes review evidence

Read the resulting observation: controller, `serviceCountdownHours`, `long`, and sample `120`. Connect each output to `bag_keys`, `mv-expand`, `set_has_element`, and `gettype`.

## 10. A second example: two zones become rows

Use the two fixture rows to make `mv-expand` tangible. The parent has two zones, so the child table has two rows with IDs 1 and 2. The next fixture's empty array creates no row.

## 11. Step 5: promote the reviewed field

Contrast the exact before and after values. `120` moves from residual JSON to the typed `ServiceCountdownHours` column only after review. Appended replay versions require explicit consumer semantics.

## 12. Adopt with evidence, not promises

Close with a one-source shadow test and measurable gates: CPU, latency, completeness, replay, array amplification, and duplicate behavior.
