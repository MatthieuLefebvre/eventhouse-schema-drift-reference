# Contributing

Keep examples synthetic, customer-neutral, and runnable in a disposable Microsoft Fabric KQL database. Never commit tenant IDs, workspace IDs, cluster URIs, tokens, customer names, or copied customer payloads.

Before opening a pull request:

1. Run `python scripts/validate_content.py`.
2. Run `python -m unittest discover -s tests/python`.
3. Regenerate the presentation with `python presentation/build_presentation.py`.
4. Describe which KQL modules were executed in Eventhouse and which remain statically reviewed.
