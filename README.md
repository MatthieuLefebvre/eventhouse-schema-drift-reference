# Eventhouse Schema Drift Reference

This repository is a customer demo and implementation guide for handling evolving IoT JSON directly in Microsoft Fabric Eventhouse. It shows how to replace recurring Spark schema-inference and flattening notebooks with native KQL processing while preserving new fields safely.

All names and data are synthetic. Validate the pattern with representative production volume before adoption.

## Start With Today's Spark Journey

Many telemetry implementations follow this path:

1. Data first lands in Eventhouse.
2. A Spark notebook reads it back through the Kusto connector.
3. Spark infers the JSON schema, flattens fields, detects changes, and writes Delta tables.
4. New fields trigger buffering, schema comparison, approval, and another merge job.

```mermaid
flowchart LR
		EH[Event Hub] --> RAW[Eventhouse landing table]
		RAW -->|Bulk connector read| EXPORT[DataExportToFile]
		EXPORT --> SPARK[Spark infer, flatten, compare]
		SPARK --> BUFFER[Drift buffer and control tables]
		SPARK --> DELTA[Typed Delta tables]
		BUFFER --> MERGE[Review and merge job]
		MERGE --> DELTA
```

This works, but it is less efficient because data leaves the engine that already stores and queries it. Every scheduled notebook adds Spark startup, bulk export, schema inference, watermark, buffer, and merge work. Concurrent connector reads can also compete for export capacity. The architecture is solving a data-shape problem with repeated data movement.

## What This Demo Proves

The demo builds the following replacement entirely inside Eventhouse:

![Eventhouse-native target architecture](docs/images/target-architecture.png)

- `RawTelemetry` keeps the original message as a replay point.
- Stored KQL functions cast approved fields into predictable columns.
- Update policies run those functions automatically when data arrives.
- Unknown fields remain in `ResidualTelemetry` rather than breaking ingestion.
- A second policy records new field names, types, samples, and first/last-seen evidence.
- Arrays become stable child rows with `mv-expand`.
- Approved fields are promoted with metadata commands and a bounded backfill.

Routine telemetry no longer needs a Spark export. Spark or a pipeline can remain as a small control-plane tool for reviewed DDL automation, external calls, or work genuinely outside KQL.

## The Four KQL Techniques To Learn

### 1. Preserve evolving JSON with `DropMappedFields`

Known routing fields become physical columns while the rest of the document remains available in `RawRecord`:

```kusto
{"Column":"MessageId", "Properties":{"Path":"$.id"}},
{"Column":"SourceType", "Properties":{"Path":"$.sourceType"}},
{"Column":"RawRecord", "Properties":{"Path":"$", "Transform":"DropMappedFields"}}
```

**Why it matters:** a producer can add a field without changing the landing-table schema or losing the new value.

### 2. Keep the target schema fixed with explicit projection and `bag_remove_keys()`

```kusto
| extend Telemetry = todynamic(RawRecord.payload.telemetry)
| project
		MessageId,
		ControllerStatus=tostring(Telemetry.controllerStatus),
		EngineHours=toreal(Telemetry.engineHours),
		ResidualTelemetry=bag_remove_keys(
				Telemetry,
				dynamic(['controllerStatus', 'engineHours', 'fuelConsumption']))
```

**Why it matters:** only named columns reach the typed table. Any new key stays in the residual bag, so the function's output shape does not change.

### 3. Run the transform automatically with an update policy

```kusto
.alter table ControllerTelemetry policy update
```
```json
[{"IsEnabled":true,
	"Source":"RawTelemetry",
	"Query":"TransformControllerTelemetry()",
	"IsTransactional":false}]
```

**Why it matters:** Eventhouse transforms each newly ingested batch without a scheduled Spark read. With `IsTransactional:false`, raw ingestion survives a target failure and operators replay from `RawTelemetry` after repair.

### 4. Turn unknown keys and arrays into rows

```kusto
| mv-expand FieldName = bag_keys(Telemetry) to typeof(string)
| where not(set_has_element(KnownKeys, FieldName))
```

```kusto
| mv-expand Zone = Zones
```

**Why it matters:** the first expression creates evidence for every unknown field; the second normalizes a variable array without creating runtime-generated columns.

## Step-By-Step Demo Journey

| Step | Run | Show the customer | Main benefit |
|---|---|---|---|
| 1 | [Landing table](kql/01-landing-table.kql) | Physical routing columns plus flexible `RawRecord` | Raw data remains recoverable |
| 2 | [JSON mapping](kql/02-json-mapping.kql) | `DropMappedFields` captures everything not already mapped | New JSON fields are retained automatically |
| 3 | [Target tables](kql/03-target-tables.kql) | Stable reporting tables and residual safety-net columns | Consumers get predictable schemas |
| 4 | [Transform functions](kql/04-flatten-functions.kql) | Explicit casts, `bag_remove_keys()`, and `mv-expand` | KQL replaces routine Spark flattening |
| 5 | [Update policies](kql/05-update-policies.kql) and [drift policy](kql/06-drift-log.kql) | Ingestion automatically fills typed tables and drift evidence | No scheduled bulk export |
| 6 | [Synthetic ingestion](kql/10-ingest-samples.kql) and [smoke tests](tests/deployed-smoke-tests.kql) | Normal fields, new fields, a type conflict, two zones, and an empty array | The audience sees the pattern survive real drift cases |
| 7 | [Promotion and backfill](kql/07-promotion-backfill.kql) | Add an approved column, revise the function, validate, and replay a bounded period | Schema evolution becomes controlled metadata work |

Use the [presenter demo script](docs/demo-script.md) for narration, expected results, questions to ask, and recovery notes.

## Safety Model

The demo policies use `IsTransactional:false`. A failed transform therefore does not roll back ingestion into `RawTelemetry`, but the corresponding target can miss rows until operators detect and replay the failure. Microsoft generally recommends transactional policies for production consistency. Choose deliberately after testing the failure and replay model.

## Demo Setup

Prerequisites:

- A Microsoft Fabric workspace with an Eventhouse and editable KQL database.
- Database Admin permission for table, function, policy, and materialized-view commands.
- A test database. The scripts create fixed demo objects.

Run the demonstration files in order:

1. `kql/01-landing-table.kql`
2. `kql/02-json-mapping.kql`
3. `kql/03-target-tables.kql`
4. `kql/04-flatten-functions.kql`
5. `kql/05-update-policies.kql`
6. `kql/06-drift-log.kql`
7. `kql/10-ingest-samples.kql`

Then run `tests/deployed-smoke-tests.kql`.

Allow approximately 25 minutes for the technical demo and 15 minutes for architecture, production risks, and questions.

## Repository Guide

- `kql/`: ordered deployment and operations modules.
- `samples/`: synthetic JSON Lines fixtures.
- `tests/`: pure-query checks and deployed smoke tests.
- `docs/`: architecture, customization, migration, and operational guidance.
- `presentation/`: generated customer presentation and reproducible source.

The [customer presentation](presentation/eventhouse-schema-drift-reference.pptx) and [target architecture image](docs/images/target-architecture.png) are generated by `presentation/build_presentation.py`.

## Important Boundaries

- Unknown keys are retained, not automatically promoted.
- Existing-key type changes are observable but require an explicit compatibility decision.
- `cooling_unit` arrays become one row per zone; the original zone identifier is retained.
- Cross-row deduplication belongs in a materialized view or query layer, not an update policy.
- OneLake availability is optional and applies to ordinary tables. Its batching latency must be validated for each consumer.

See [Architecture](docs/architecture.md) for the end-to-end flow and [Customization Guide](docs/customization-guide.md) before adapting this sample.

## Microsoft Learn References

- [Update policy overview](https://learn.microsoft.com/kusto/management/update-policy?view=microsoft-fabric)
- [Ingestion mappings and DropMappedFields](https://learn.microsoft.com/kusto/management/mappings?view=microsoft-fabric)
- [bag_remove_keys()](https://learn.microsoft.com/kusto/query/bag-remove-keys-function?view=microsoft-fabric)
- [mv-expand operator](https://learn.microsoft.com/kusto/query/mv-expand-operator?view=microsoft-fabric)
- [Create materialized views](https://learn.microsoft.com/kusto/management/materialized-views/materialized-view-create?view=microsoft-fabric)
- [OneLake availability](https://learn.microsoft.com/fabric/real-time-intelligence/event-house-onelake-availability)
