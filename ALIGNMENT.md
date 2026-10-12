# Alignment Audit (Rules 85-100 / 16 items) — json-output-salvage v0.1.1

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Safety/Ethics section | N/A | Not a security-research repo; no dual-use surface; `salvage()` never raises and returns `ok:false` on unrepairable input; README FAQ warns against using it for safety-critical decisions |
| 2 | Privacy/dezero | PASS | No secrets/tokens/real names in any file; only contact line uses hcac4735@agent.qq.com (README License section); grep `(sk-\|ghp_\|api[_-]?key\s*=\s*['"][A-Za-z0-9])` → 0 hits |
| 3 | Copyright boundary | PASS | Comparisons (strict loads, json5, re-prompting) are structural restatements of public knowledge; no >50-char copied text; MIT LICENSE present, "zhengming contributors" |
| 4 | Fact-check annotation | PASS | 72-check suite "~3 s" marked [Measured] with repro `python self_test.py`; other timings marked ~; "often the best fix" re-prompt claim framed qualitatively |
| 5 | Confidence grading | PASS | Opener [High ≥80%] tied to the suite; worst-case-behavior claims tied to parse-verified acceptance design; ≥2 explicit labels |
| 6 | PLAN B built-in | PASS | "Minimal Fallback (PLAN B)" section: strict-parse sanity gate + sed fence stripping, zero setup |
| 7 | Timeout preset | PASS | Quickstart states "~2 min" with ~1 s / ~3 s step markers |
| 8 | Rule-conflict arbitration | PASS | "Design Trade-offs" opens with priority order: never-corrupt (parse-verified) > auditability > repair coverage > performance |
| 9 | Version changelog | PASS | CHANGELOG.md v0.1.0 + v0.1.1; v0.1.1 records documentation completion and suite re-verification |
| 10 | Exemption instruction | N/A | Session-level rule; static repo content not applicable |
| 11 | External-knowledge cutoff | PASS | "No direct equivalent found as of 2026-10-12" stated explicitly in why-not-X |
| 12 | Assumption explicitness | PASS | "[Core Assumptions]" section with 4 items |
| 13 | Logic-check trio | PASS | self_test.py three-tier suite (functional / error / extreme-edge, incl. non-string input, 8-pass budget, deep truncation); `python self_test.py` → `SUMMARY: PASS 72/72` |
| 14 | Socratic question | PASS | FAQ "When NOT to use this tool?" with 4 anti-use-cases (re-prompting possible, safety-critical, semantic repair, non-JSON input) |
| 15 | Pareto improvement | PASS | v0.1.1 documentation round: README articulates the parse-verified acceptance contract and audit-trail semantics that the module docstring only sketches; traceable in CHANGELOG |
| 16 | Ultimate fallback (≤60-word opener) | PASS | First paragraph = 60 words, contains what-it-is and the "recovery instead of an exception" judgment sentence |

Second-order effects (rule 16 bonus): PASS — "Limits & Second-order Effects" covers invisible-failure normalization, repair-rate-as-regression-signal, and salvaged-but-wrong cache poisoning.

Scan evidence: `grep -rEn "(sk-|ghp_|api[_-]?key\s*=\s*['\"][A-Za-z0-9])" .` → 0 hits; `grep -rn "hcac4735@agent.qq.com" README.md` → 1 hit.
