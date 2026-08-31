# Architecture

## Current Export-Based Pattern

```mermaid
flowchart LR
    EH[Event Hub] --> RAW[Eventhouse landing table]
    RAW -->|Kusto Spark connector\nDataExportToFile| SPARK[Spark schema inference and flattening]
    SPARK --> CHECK{Drift detected?}
    CHECK -->|No| DELTA[Typed Delta tables]
    CHECK -->|Yes| BUFFER[Parquet buffer and control table]
    BUFFER --> REVIEW[Manual review]
    REVIEW --> MERGE[Spark merge]
    MERGE --> DELTA
```

The large connector read is the capacity-sensitive boundary. The buffering, watermark, and target-schema reconciliation logic exists because processing left Eventhouse.

## Eventhouse-Native Target

```mermaid
flowchart LR
    EH[Event Hub] --> RAW[RawTelemetry]
    RAW --> C[Controller update policy]
    RAW --> G[Gateway update policy]
    RAW --> U[Cooling unit update policies]
    RAW --> D[Drift observation policy]
    C --> CT[ControllerTelemetry]
    G --> GT[GatewayTelemetry]
    U --> UT[CoolingUnitTelemetry]
    U --> ZT[CoolingUnitZones]
    D --> DL[TelemetryDriftObservations]
    CT -. optional .-> OL[OneLake availability]
    GT -. optional .-> OL
    UT -. optional .-> OL
    ZT -. optional .-> OL
    DL --> APPROVE[Reviewed promotion workflow]
    APPROVE --> DDL[Add column and revise function]
    DDL --> BACKFILL[Bounded Eventhouse backfill]
```

Every update-policy function returns a fixed schema. New telemetry keys remain in `ResidualTelemetry` and are also recorded as drift observations. No routine telemetry export is required.

## Per-Record Processing

```mermaid
sequenceDiagram
    participant Source as Event source
    participant Raw as RawTelemetry
    participant Policy as Update policies
    participant Typed as Typed tables
    participant Drift as Drift observations
    Source->>Raw: JSON using RawTelemetryJsonMapping
    Raw->>Policy: New extent triggers policies
    Policy->>Typed: Known fields plus residual bag
    Policy->>Drift: Unknown field observations
    Note over Raw,Drift: IsTransactional=false keeps raw ingestion independent of target success
```

## Design Boundaries

- Update policies perform per-ingestion transformations, not cross-row upserts.
- Drift observation is append-only; `ReviewTelemetryDrift()` aggregates duplicates.
- Variable arrays are normalized to rows. Empty arrays intentionally create no zone rows.
- Promotion is a controlled metadata operation, never an automatic reaction to one sample.