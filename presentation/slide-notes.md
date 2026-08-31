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

## 5. The seven-step demo journey

Preview exactly what the audience will see. This makes the later code feel like a sequence of proofs instead of disconnected KQL files.

## 6. Technique 1: preserve future fields

Explain `Path:"$"` as the whole JSON document. `DropMappedFields` removes envelope values already mapped to physical columns while preserving the rest.

## 7. Technique 2: guarantee a fixed output

This is the decisive drift-tolerance pattern. Explicit projection fixes the output contract; `bag_remove_keys` preserves every unknown value in the residual bag.

## 8. Technique 3: remove the scheduled export

An update policy reacts to ingestion and calls a stored function. Explain the deliberate `IsTransactional:false` availability tradeoff and required replay monitoring.

## 9. Technique 4: detect keys and expand arrays

The same row-expansion primitive handles both unknown key names and array items. No runtime-generated columns are required.

## 10. Live proof: what the customer should see

Pause on each expected result. The strongest proof is that a new field reaches the residual and drift review while normal typed processing continues.

## 11. Governed promotion stays simple

Promotion is not automatic. Add the column, revise the function, compare schemas, and replay a bounded interval. Appended versions require explicit consumer semantics.

## 12. Adopt with evidence, not promises

Close with a one-source shadow test and measurable gates: CPU, latency, completeness, replay, array amplification, and duplicate behavior.
