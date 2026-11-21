# ADR 011 — Runner-built releases (headless apkg builder)

Supersedes ADR 009's live-deck export step; amends ADR 004.

## Context

The release artifact was exported from the maintainer's live Anki collection
via Anki-Connect (`export_apkg.py`), which made the desktop the only machine
able to produce a release. That has two costs:

- Releases stall when the desktop's upstream network misbehaves (uploads to
  `uploads.githubusercontent.com` can fail while API calls are healthy).
- Every other repository the maintainer owns publishes from CI runners; this
  one could not, because the sample content lived only in the live collection.

The earlier live-deck export also shipped the whole study deck by accident
(42 real cards in `v0.1.4`–`v0.1.8`). The `--release` tag gate and the
dedicated release deck fixed the leak, but the artifact still depended on the
desktop.

## Decision

1. **Sample content becomes repo content.** `fetch_sample_deck.py` derives
   `samples/notes.json`, `samples/fields.json`, `samples/media.json`, and
   `samples/media/` from the live release deck
   (`My Life Decks::Chinese::anki-chinese-template`) via Anki-Connect —
   machine-derived, never hand-written. `samples/fields.json` snapshots the
   field names plus per-field font/size/description, and tests validate it
   against the field references in the templates so it cannot silently drift.
2. **Headless stdlib builder.** `build_sample_apkg.py` builds
   `dist/anki-chinese-template.apkg` with stdlib only (`sqlite3` +
   `zipfile`): a legacy Anki 2.0-format package (schema-11
   `collection.anki2`, numeric media entries, `media` index, no `meta` file).
   The note type is composed from the repo templates + CSS + the committed
   field snapshot; notes/cards/media come from `samples/`. Identifiers are
   sha-derived from stable names, note guids are content hashes, and note
   mtimes encode the CSS version stamp — so a later release re-imports as an
   update instead of duplicating.
3. **CI publishes.** `.github/workflows/release.yml` runs on a `v*` tag push:
   it runs `./verify`, builds the apkg from the tagged commit, and publishes
   the GitHub release with the asset. The desktop never builds or uploads the
   release asset.
4. **`finish.sh` keeps the inherently local parts.** verify → version stamp →
   `sync_to_anki.py` (with snapshots) → commit → push main → push tag. It
   never builds or uploads the artifact: `./verify` already builds and
   validates the apkg on every run.

The live release deck is still where the maintainer curates which cards ship
(`seed_sample_cards.py` for a fresh profile, `curate_release_cards.py` for a
few real cards). `fetch_sample_deck.py` snapshots that deck into the repo; the
release itself no longer reads Anki.

## Consequences

- Releases no longer depend on the desktop's network or a running Anki; CI
  builds and publishes them from the tagged commit.
- The repo gains the sample fixtures (~0.6 MB for the 5 curated cards:
  `notes.json` carries the glossary HTML, media is ~0.1 MB). The content is
  already public via the release assets.
- The builder's legacy-format output must be import-validated against current
  Anki in a scratch profile for the first CI-built release. Fallback if a
  future Anki refuses the legacy shape: also emit an uncompressed
  `collection.anki21` twin (Version::Legacy2, still schema 11).
- ADR 009's hard-won verification insight is preserved: the builder tests
  independently re-open the artifact, check `collection.anki21` semantics,
  and validate the note type, deck tree, note/card rows, media byte-equality,
  and deterministic rebuilds. `export_apkg.py` and `tests/test_apkg.py` are
  retired.
- The Chinese warm accent and the 5 curated release cards are unchanged.

## Verification (2026-11-21)

`python3 build_sample_apkg.py --check` → `v0.2.0, 5 notes, 6 media files,
0.2 MB`; `tests/test_sample_apkg.py` → 36/36 (zip layout, schema-11
collection, model byte-equality with the repo templates, field metadata,
deck tree, note/card shapes, guids/checksums, media equality, determinism).
A real Anki import of the CI-built artifact is the remaining one-time check
for the first tagged release.