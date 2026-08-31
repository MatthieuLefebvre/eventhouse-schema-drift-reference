# OneLake Quick Win

If OneLake availability is enabled on the Eventhouse landing table, a Spark notebook can read its Delta representation directly instead of using the Kusto Spark connector. This can remove routine `DataExportToFile` operations before the native update-policy migration is complete.

Validate first:

1. Run `.show table RawTelemetry policy mirroring`.
2. Inspect table mirroring operations and observed latency.
3. Confirm that consumers accept adaptive batching. Microsoft documents a default delay of up to three hours or until files are approximately 200-256 MB, configurable from 5 minutes to 3 hours.
4. Compare a bounded interval between Eventhouse and the Delta representation.

OneLake availability is not a zero-latency streaming interface. While enabled, tables cannot be renamed or have column types altered; adding and deleting columns is supported. The Delta representation is read-only.

Reference: [OneLake availability](https://learn.microsoft.com/fabric/real-time-intelligence/event-house-onelake-availability).
