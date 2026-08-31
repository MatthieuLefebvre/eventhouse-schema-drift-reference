# Presenter Demo Script

This script supports a 25-minute technical demonstration followed by architecture and production-readiness discussion. Practice it once in a disposable Eventhouse database and keep the KQL files open in numeric order.

## Demo Outcome

By the end, the customer should be able to explain four points:

1. Eventhouse can flatten known JSON fields without a recurring Spark export.
2. New fields do not break fixed target schemas when they remain in a residual dynamic bag.
3. Update policies can route and transform new data automatically.
4. KQL can surface unknown keys and normalize arrays while field promotion remains governed.

## Before the Meeting

- Create or select a disposable KQL database.
- Confirm Database Admin permission.
- Open files `01` through `07`, then `10` and the smoke tests.
- Run cleanup only if this demo was deployed previously.
- Keep [the architecture](architecture.md) visible for the transition from problem to solution.
- Do not promise production capacity results. Have the customer's message rate, payload size, concurrency, duplicate window, and replay requirements ready as follow-up questions.

## 0-3 Minutes: Establish Today's Spark Pattern

**Show:** the current export-based architecture in [architecture.md](architecture.md).

**Say:**

> Today, data lands in Eventhouse and a Spark notebook reads it back through the Kusto connector. Spark starts a session, exports a batch, infers JSON, flattens it, compares schemas, manages watermarks and buffers, and writes another store. The logic works, but routine processing repeatedly moves data out of the engine that already understands JSON and KQL.

Emphasize that this is not an argument against Spark. Spark remains appropriate for ML, external libraries, and broad Lakehouse processing. The inefficiency is using a bulk export plus notebook orchestration for per-message parsing, routing, and drift evidence that Eventhouse can perform during ingestion.

**Ask:**

- How many notebooks can read the same landing table concurrently?
- How much time is Spark startup versus transformation?
- Which steps exist only to manage the exported batch?

## 3-5 Minutes: Show the Destination

**Show:** the Eventhouse-native architecture in [architecture.md](architecture.md).

**Say:**

> The replacement keeps an original raw row, then lets several update policies react independently. Typed tables serve normal analytics, a child table handles arrays, and a drift table records unknown fields. No scheduled notebook has to export the telemetry batch. Promotion is still governed; we are changing where data-plane work runs, not removing review.

## 5-7 Minutes: Create the Raw Inbox

**Run:** [01-landing-table.kql](../kql/01-landing-table.kql).

**Highlight:**

```kusto
RawRecord:dynamic
```

**Say:**

> The landing table has physical columns only for stable values needed to identify and route a message. `RawRecord` is the flexible safety net. If downstream logic fails or a field is promoted later, we can replay from the original message.

**Benefit:** separates durable raw ingestion from evolving analytical contracts.

## 7-9 Minutes: Preserve Unmapped JSON

**Run:** [02-json-mapping.kql](../kql/02-json-mapping.kql).

**Highlight:**

```kusto
{"Column":"RawRecord", "Properties":{"Path":"$", "Transform":"DropMappedFields"}}
```

**Say:**

> `DropMappedFields` puts known envelope values in dedicated columns and keeps the rest of the document in `RawRecord`. A producer can add a payload key tonight without requiring an emergency landing-table alteration.

**Benefit:** future fields are retained without duplicating already mapped envelope values.

## 9-11 Minutes: Define Stable Consumer Tables

**Run:** [03-target-tables.kql](../kql/03-target-tables.kql).

**Highlight:** `ResidualTelemetry:dynamic` and `ResidualZone:dynamic`.

**Say:**

> These tables are deliberately predictable for BI, APIs, and mirrored Delta consumers. The residual columns are not error buckets. They are governed holding areas for valid but not-yet-promoted data.

Point out that `CoolingUnitZones` stores one row per zone. It avoids creating `Zone1`, `Zone2`, and future `ZoneN` columns as array sizes change.

**Benefit:** stable contracts for consumers without discarding drifted data.

## 11-15 Minutes: Replace Spark Flattening With KQL

**Run:** [04-flatten-functions.kql](../kql/04-flatten-functions.kql).

**Highlight these three techniques:**

```kusto
| extend Telemetry = todynamic(RawRecord.payload.telemetry)
```

```kusto
ControllerStatus=tostring(Telemetry.controllerStatus),
EngineHours=toreal(Telemetry.engineHours)
```

```kusto
ResidualTelemetry=bag_remove_keys(
    Telemetry,
    dynamic(['controllerStatus', 'engineHours', 'fuelConsumption']))
```

**Say:**

> This is the central schema-drift technique. We name and cast every approved output, then remove those known keys from the original bag. Anything new remains in `ResidualTelemetry`. The input can evolve, but the function still returns the exact columns and order expected by the target table.

Then show:

```kusto
| mv-expand Zone = Zones
```

**Say:**

> `mv-expand` creates one row per array element. KQL handles the variable zone count directly; Spark does not need to discover zone numbers and generate columns.

**Benefits:** fixed output schema, explicit type contracts, residual preservation, and native array normalization.

## 15-17 Minutes: Make It Automatic

**Run:** [05-update-policies.kql](../kql/05-update-policies.kql).

**Highlight:**

```json
{"Source":"RawTelemetry",
 "Query":"TransformControllerTelemetry()",
 "IsTransactional":false}
```

**Say:**

> The policy connects new raw ingestion to the saved KQL function. There is no schedule, watermark query, or bulk connector read. `IsTransactional:false` intentionally protects raw ingestion if one target fails. That trades target atomicity for raw availability, so monitoring and replay are mandatory.

**Benefit:** removes scheduled export orchestration while preserving a recovery path.

## 17-19 Minutes: Detect Drift Natively

**Run:** [06-drift-log.kql](../kql/06-drift-log.kql).

**Highlight:**

```kusto
| mv-expand FieldName = bag_keys(Telemetry) to typeof(string)
| where not(set_has_element(KnownKeys, FieldName))
```

**Say:**

> `bag_keys` lists the fields that actually arrived. `mv-expand` turns those names into rows, and `set_has_element` filters out the approved list. The result records the unknown path, observed type, sample value, and event time during ingestion.

Show `ReviewTelemetryDrift()` and explain that repeated observations are summarized at query time rather than requiring a Spark anti-join before every write.

**Benefit:** incremental drift evidence with no historical export scan.

## 19-22 Minutes: Ingest and Prove the Behavior

**Run:** [10-ingest-samples.kql](../kql/10-ingest-samples.kql), then [deployed-smoke-tests.kql](../tests/deployed-smoke-tests.kql).

Walk through the expected evidence:

- Six raw records across three source types.
- Controller output contains a residual `serviceCountdownHours` value.
- Gateway's incompatible `signalStrength` becomes null after `toint`, while the original remains in `RawRecord` for investigation.
- One cooling-unit message creates two zone rows with original zone IDs.
- An empty zones array creates no child rows.
- Drift review includes `serviceCountdownHours`, `modem`, and `compressorHealth`.

**Say:**

> The critical observation is that typed ingestion continues even when a new key arrives. The new value is both preserved and surfaced for review. That is the behavior the Spark buffer was providing, now implemented directly in Eventhouse.

## 22-25 Minutes: Promote a Reviewed Field

**Open, but do not blindly run:** [07-promotion-backfill.kql](../kql/07-promotion-backfill.kql).

Explain each command:

```kusto
.alter-merge table ControllerTelemetry (ServiceCountdownHours:real)
```

Adds the approved physical column without rebuilding the table.

```kusto
.create-or-alter function ... TransformControllerTelemetry()
```

Revises future processing so the field moves from the residual bag into its own column.

```kusto
TransformControllerTelemetry | getschema
.show table ControllerTelemetry schema as json
```

Compares function output with the target contract before relying on the policy.

```kusto
.set-or-append ControllerTelemetry <| ...
```

Reprocesses only the approved historical interval inside Eventhouse. Explain that this appends newer row versions because Kusto extents are immutable; use the optional latest-record view or a replacement-table migration when consumers require one physical version.

**Benefit:** promotion is metadata plus bounded Eventhouse processing, not another bulk Spark flattening pipeline.

## Optional Modules

| Script | When to show it | Customer value |
|---|---|---|
| [00-cleanup-demo.kql](../kql/00-cleanup-demo.kql) | Before rehearsals or after the workshop | Safely resets only the disposable demo objects |
| [08-optional-dedup.kql](../kql/08-optional-dedup.kql) | When discussing retries and appended backfill versions | Shows latest-record materialization; lookback must come from measured duplicate behavior |
| [09-monitoring.kql](../kql/09-monitoring.kql) | During production-readiness discussion | Shows policy configuration, failures, completeness counts, and OneLake mirroring status |
| [pure-query-tests.kql](../tests/pure-query-tests.kql) | When object creation is not permitted | Demonstrates residual bags and array expansion without persistent objects |

## Close the Demo

**Say:**

> The proposal is not that KQL replaces every Spark workload. It replaces this specific recurring data-plane loop: export, infer, flatten, compare, buffer, and merge. Raw data remains available, consumers get stable tables, drift remains visible, and promotion stays controlled. The next step is a one-source shadow test at representative peak load.

End with production questions:

- What is the required raw replay horizon?
- Which type conflicts should be quarantined versus converted to null?
- What is the maximum array size and resulting row amplification?
- What duplicate-arrival window should size any materialized-view lookback?
- Is OneLake batching latency acceptable for each downstream consumer?
- What ingestion CPU and latency are observed at peak concurrency with all policies enabled?
