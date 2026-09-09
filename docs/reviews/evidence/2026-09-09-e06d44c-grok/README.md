# Independent grok probes for MACAO commit e06d44c (Round 4)

- **issue_ids**: grok/P1-1 prior residual, grok/P1-2 adopt E1, grok/P2 empty-evidence & prefix-escape, grok/L4-OPS
- **commit**: `e06d44cb31a0dbcbe199e6bb124430e9701e087f`
- **platform**: Linux; Python 3.10+; git; no network; no vendor CLI
- **last_executed**: 2026-09-09T00:44:04+08:00
- **isolation**: each probe uses `tempfile.mkdtemp()`; host repo is not mutated by the scripts

## Scripts

| Script | What it verifies |
|---|---|
| `probe_e06d44c.py` | Prior P1-1 battery + empty/missing evidence_commit + path-prefix sibling + adopt deadbeef/E2_ADOPT + doctor rc + F-26 Claude no-cwd + live_runner mock observation |

Re-run:

```bash
cd /home/debian/macao
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-09-e06d44c-grok/probe_e06d44c.py
PYTHONPATH=src python3 docs/reviews/evidence/2026-09-08-7bc8d70-grok/probe_checkpoint_p104.py
```

Also re-ran (not copied): Claude `probe_checkpoint_and_adopt.py`, Qwen `repro_7bc8d70_qwen.py`.
Codex `reproduce_fail_closed_gaps.py` still asserts the *old* fail-open (`exit_code == 0` for `deadbeef`); after the fix it raises `AssertionError` — it is a bug-reproduction script, not a closure verifier.
