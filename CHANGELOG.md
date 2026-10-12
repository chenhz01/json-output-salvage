# Changelog

## v0.1.1 — 2026-10-12
- Documentation layer completed: README (Problem / How it works / Quickstart / why-not-X with the dated no-equivalent statement / Minimal Fallback / Trade-offs / Limits / FAQ), ALIGNMENT.md 16-item audit.
- Self-test re-verified green, no code changes needed this round: `python self_test.py` → `SUMMARY: PASS 72/72`.

## v0.1.0 — 2026-10-11
- Initial implementation: ordered repair pipeline (prose/fence stripping, positional smart-quote normalization, guarded single-quote conversion, trailing-comma removal, bracket-stack truncation completion), parse-verified acceptance with audit trail, `salvage()` API (never raises), CLI (file/stdin/`--text`, `--json`, exit 0/1/2 contract).
- Self-test suite (functional / error / extreme-edge tiers).
