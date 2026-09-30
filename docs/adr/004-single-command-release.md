# ADR 004 — Single-command release with pre-sync snapshots

## Context

Multi-step endings (test → sync → export → commit → push → release) were
dropped late in sessions when run manually.

## Decision

`finish.sh` runs the full chain in deterministic order and stops on first
failure: `verify → version stamp → sync_to_anki.py → build_apkg.py →
commit → push main → gh release create --target main → fetch tag`. The tag
points at the exact pushed commit. `./verify` is the side-effect-free
subset it delegates to. `sync_to_anki.py` snapshots the live Anki state to
`backups/<timestamp>/` (microsecond stamps) before overwriting and aborts
on empty live state. `build_apkg.py` writes the apkg into gitignored
`dist/` **and verifies it before returning**; the apkg ships as a GitHub
Release asset, never in the repo. No-op runs never publish.

> **Amended by ADR 009.** This ADR originally specified
> `release_apkg.py` → Anki-Connect `exportPackage`. That action is
> broken on Anki 26.x (it silently exports the Default deck while
> reporting success), so step 3 is now `build_apkg.py`: the package is
> written in-repo with stdlib `sqlite3`/`zipfile` and re-opened for
> verification. The ordering, the snapshots, and the no-op protection
> above are unchanged.

## Consequences

One command to remember; snapshots make Anki-side overwrites recoverable;
tag, tree, and live templates agree (CSS header is stamped before sync).
Push-before-release ordering guarantees the tag commit == the pushed
commit on main. A wrong release asset is now impossible to ship silently:
the export step fails loudly before commit.
