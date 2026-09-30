# ADR 009 — Build the apkg in-repo instead of calling Anki-Connect's exporter

Status: accepted · Date: 2026-09-30

## Context

ADR 004 made the release a single command whose export step is
`release_apkg.py` → Anki-Connect `exportPackage`. That is the "only verified
export action" the add-on exposes, and it worked when the Japanese repo was
set up.

It does not work here, and it fails **silently**.

- Anki is **26.09.3**. The installed Anki-Connect build declares
  `max_point_version: 45` (Anki 25.x), so it is out of support for this Anki.
- Its `exportPackage` does:

  ```python
  deck = collection.decks.by_name(deck)
  if deck is not None:
      exporter = AnkiPackageExporter(collection)
      exporter.did = deck['id']      # assigned AFTER construction
      exporter.exportInto(path)
      return True                     # success, unconditionally
  ```

  On the 26.x backend, `did` set after construction is ignored. The call
  returns `True` and writes a **valid-looking apkg containing the Default
  deck**.

Observed concretely: requesting
`My Life Decks::Japanese::anki-japanese-template` (11 cards) and
`My Life Decks::Chinese` (3 cards) both produced a 53 KB apkg containing
`Basic`, `Cloze`, `Image Occlusion` and one card from `Default`. None of our
note types, none of our cards, no error.

The first `finish.sh` run of this repo would therefore have published a
release asset that installs the wrong templates while reporting success.

A second, independent trap: an **empty** target deck also degrades to the
Default deck, so "the deck exists" is not evidence that the export worked.

## Decision

**Build the apkg in-repo** (`build_apkg.py`, stdlib `sqlite3` + `zipfile`),
and **verify the file after writing it**.

- Reads (model, templates, CSS, the deck's notes) still go over
  Anki-Connect — that part of the add-on works fine.
- Writing is ours: a schema-11 `collection.anki21` with our `col`, `notes`,
  `cards`, `revlog`, `graves` tables, zipped with `meta` and `media`.
  Deterministic ids, so rebuilds are reproducible.
- `verify_apkg()` re-opens the zip it just wrote and asserts the note type
  name, the deck name, and the note count. A mismatch is a **hard failure**
  that aborts `finish.sh` before anything is committed, pushed, or
  published.
- An empty target deck is an explicit error with the fix in the message
  (`seed_sample_cards.py`), never a silent fallback.

`tests/test_apkg.py` covers the builder in CI (no Anki needed) and — the
part that matters — asserts that `verify_apkg` **rejects** a package with
the wrong model name and a wrong note count, and that it says why. A gate
that cannot fail is not a gate.

## Alternatives rejected

- **Use Anki's GUI export** (File → Export → `.apkg`) and attach manually.
  Not automatable, not reproducible, and `finish.sh` loses its
  single-command property.
- **Patch/upgrade the AnkiConnect add-on.** The right long-term fix, but it
  is a change to the user's Anki installation, not to this repository, and
  the release loop must not depend on a version of the user's environment
  that we do not control. Worth doing separately; not a release dependency.
- **Trust the exporter and move on.** The failure is silent, so there is
  no signal to notice. Unacceptable for the one artifact other people
  install from.

## Consequences

- `finish.sh` step 3 is now `build_apkg.py`; `release_apkg.py` is deleted.
  ADR 004's chain is amended, not replaced — the ordering, snapshots, and
  no-op protection are unchanged.
- The apkg contains no media. The sample deck is text-only, so `media` is
  the empty map; a deck with images would need the media entries added
  here, and the absence of a media-fidelity test is a real limitation
  rather than a solved problem.
- Scheduling state is not exported (`includeSched: false` in spirit, and
  the sample cards are new), matching the previous behaviour.
- If the AnkiConnect add-on is ever updated and `exportPackage` verified
  again, this can be replaced — but only after a test proves the exporter
  honours the deck name on this Anki version.
