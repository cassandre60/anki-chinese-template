# ADR 009 — Verify the exported apkg, and read `collection.anki21`

Status: accepted · Date: 2026-09-30 · **corrects an earlier draft of this ADR**

## Context

The release loop's export step produces the one artifact other people
install. ADR 004 made it `release_apkg.py` → Anki-Connect `exportPackage`,
which is the only export action the add-on exposes.

While bootstrapping this repository I concluded that `exportPackage` was
**broken** on this machine: I opened the exported package, found `Basic`,
`Cloze` and `Image Occlusion` note types with a single card in the Default
deck — none of ours — and wrote a whole apkg builder to replace it.

**That conclusion was wrong.** `exportPackage` works correctly here. The
deck limiter is honoured and the package contains the Chinese note type,
the Chinese deck, and every card in it.

## What actually went wrong

An apkg is a zip containing **two** SQLite databases:

| entry | what it is |
| --- | --- |
| `collection.anki21` | the legacy schema that **holds the exported content** |
| `collection.anki2` | a vestigial companion holding a **fixed set of stock note types** (Basic, Cloze, Image Occlusion…) and one Default-deck card |

Both files are present in every package Anki writes. I inspected
`collection.anki2`. For a perfectly good Chinese package it reports stock
note types and one Default card — exactly what I "found". The real content
was sitting in `collection.anki21` the whole time, unread.

So: not an exporter bug, and not an Anki/Anki-Connect version mismatch. A
verification bug. The version mismatch was real but irrelevant —
AnkiConnect declares `max_point_version: 45` (Anki 25.x) while Anki is
26.09.3, yet six back-to-back large exports (including three 5.9 MB ones)
completed without incident.

The cost of the wrong conclusion was real: a hand-rolled apkg writer
replaced a working, battle-tested exporter for one release.

## Decision

**Use `exportPackage` again. Keep the verification, and fix it.**

`export_apkg.py` is two steps:

1. **Export** via `exportPackage` into gitignored `dist/`.
2. **Verify** by re-opening the zip, reading **`collection.anki21`**, and
   asserting: our note type is present, the Chinese deck is present, and
   the note count equals the live card count. Any mismatch is a **hard
   failure** that aborts `finish.sh` before commit, push, or release.

Verification is kept because of a failure mode that is real and silent:

> **An empty deck exports as a package containing no note type at all.**
> Verified: `exportPackage` on a zero-card deck returns `True` and writes
> a valid 53 KB package with `models: []`. It imports cleanly and installs
> nothing. A user who follows the release notes, imports the apkg, and
> deletes the sample cards, would be left with an empty apkg and no error
> anywhere.

Success is therefore not evidence. `export_apkg.py` also refuses up front
when the live deck has zero cards, and names the fix
(`seed_sample_cards.py`).

`tests/test_apkg.py` pins all of it, including the regression:

- builds an apkg shaped exactly like Anki's (real content in
  `collection.anki21`, stock types in `collection.anki2`);
- asserts that reading `collection.anki2` would have missed our note type
  and that reading `collection.anki21` finds it;
- asserts the verifier **rejects** an empty-note-type package, a wrong note
  type, a note-count mismatch, a missing deck, and a truncated zip — and
  says why in each case. A gate that cannot fail is not a gate.

## Consequences

- `build_apkg.py` is deleted; `export_apkg.py` replaces `release_apkg.py`.
  The hand-rolled writer is gone, and with it its untested corners (media
  entries, scheduling state, id collisions) — all of which Anki's own
  exporter already handled.
- ADR 004's chain is unchanged apart from the step-3 script name; the
  ordering, the pre-sync snapshots, and the no-op protection stand.
- The lesson is recorded here and in `export_apkg.py`'s docstring because
  it is the kind of mistake that is invisible on the second occurrence: a
  wrong-asset *diagnosis* is as dangerous as a wrong asset, and it costs a
  working dependency to act on.
- Residual limit: the package contains no media, because the sample deck is
  text-only. A deck with images would still be exported by Anki's exporter,
  so this is a property of the sample deck, not of the tool.

## Still worth doing (outside this repo)

The installed AnkiConnect is out of support for Anki 26.09.3
(`max_point_version: 45`). It works, and six consecutive exports proved
that, but an unsupported add-on is a real risk for the user's collection.
Updating it is a change to their Anki installation, not to this
repository, and is not a release dependency.
