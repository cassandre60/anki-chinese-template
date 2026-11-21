# IMPLEMENTATION_PLAN.md — task graph + status

The graph is part of the plan (not a substitute): the graph says *what
depends on what*, the task entries say *what each node means*. This is a
task/slice graph, not a todo list (`Build frontend` would not qualify).

## Where this repo came from

`anki-chinese-template` is a **language port** of
[`anki-japanese-template`](https://github.com/cassandre60/anki-japanese-template).
Tasks T1-T17 (the whole front/back/compactor/audioscape/release history) are
inherited and are COMPLETE by construction — the code came across. They are
listed here for provenance, not as work.

The **port** is a separate, short graph below. Only its nodes are open work.

## Port task graph (complete)

```text
                  ┌──────────────────────────┐
                  │ P0 model + deck in Anki  │
                  │ (bootstrap_chinese_model)│
                  └────────────┬─────────────┘
                               │
              ┌────────────────┴────────────────┐
              ↓                                 ↓
   ┌──────────────────────┐          ┌──────────────────────┐
   │ P1 front template    │          │ P2 back template     │
   │ labels only          │          │ Pinyin field + hero  │
   │ (language-agnostic)  │          │ + tone controller    │
   └──────────┬───────────┘          └──────────┬───────────┘
              │                                 ↓
              │                    ┌──────────────────────────┐
              │                    │ P3 stylesheet: fonts,   │
              │                    │ tones §9, §5c, compactor│
              │                    │ §6b Chinese selectors   │
              └──────────┬─────────┴──────────┬──────────────┘
                         ↓                    ↓
              ┌──────────────────┐  ┌──────────────────────┐
              │ P4 test suite    │  │ P5 docs: PRODUCT,    │
              │ retarget + new   │  │ ARCHITECTURE, QUALITY│
              │ pinyin_tones     │  │ ADRs 007/008, README │
              └────────┬─────────┘  └──────────┬───────────┘
                       ↓                        ↓
              ┌────────────────────────────────────────┐
              │ P6 ./verify + visual review            │
              └────────────────┬───────────────────────┘
                               ↓
              ┌────────────────────────────────────────┐
              │ P7 release (finish.sh) + gh repo      │
              └────────────────────────────────────────┘
```

Dependencies: `P0 → {P1, P2} → {P3, P4} → {P5, P6} → P7`. P1 and P2 are
parallelizable; P3 must follow P2 (the Pinyin rules need the markup).

## Port tasks

- **P0 — Note type + deck in local Anki.** `bootstrap_chinese_model.py`
  creates `Chinese Note type (Sentence card by Default)` (18 fields, one
  `Card 1`) and deck `My Life Decks::Chinese`;
  `set_field_descriptions.py` writes the Fields-dialog text. The Japanese
  note type is untouched. Status: COMPLETE (run 2026-09-30, Anki live).
- **P1 — Front template: labels.** All visible strings and `title`/`aria-label`
  values become Chinese (`例句` / `词语`, `播放例句语音`, `播放词语语音`).
  Every branch, the cloze fixup, Policy B and Mature Word Mode are
  language-agnostic and were ported unchanged.
  Status: COMPLETE.
- **P2 — Back template: Pinyin + tones.** `{{edit:furigana:…}}` filters
  dropped; `Pinyin` rendered as `.pinyin-display` under the headword inside a
  column-direction `.hero-word-wrap`; `Sentence Pinyin` added under the
  sentence; `Pitch Accent` removed; `applyPinyinTones()` added (diacritic +
  numeric detection, `tone-0..4`, idempotent, markup-safe); `P` replaces `F`;
  `Kanji Notes` → `Hanzi Notes`; all strings Chinese.
  Status: COMPLETE (`tests/test_pinyin_tones.py` 16/16).
- **P3 — Stylesheet.** CJK font stacks + tone-mark-safe Latin stack
  (`--font-pinyin`); `--tone-0..4` palette in both themes; §5c Pinyin line;
  §9 repurposed from ruby to tones; §9b from "pin all furigana" to the `P`
  hide rule; `.hero-word-wrap` column; §6b compactor reduced to Chinese
  structural selectors; `.sentence-japanese` → `.sentence-chinese`;
  `--furigana-headroom` demoted to a generic clearance token (the scenic
  band's 12px tuck is now an explicit padding).
  Status: COMPLETE.
- **P4 — Test suite.** Japanese fixtures replaced with hand-authored Chinese
  ones; `test_templates.py` reading-ban + tone/pinyin checks; new
  `test_pinyin_tones.py`; `test_layout.py` ruby-overlap probes replaced with
  Pinyin-stacking probes; `test_back_more.py` / `test_yukei.py` retargeted
  (incl. the `google-chrome` binary name).
  Status: COMPLETE (`./verify` 302/302 green).
- **P5 — Documentation.** PRODUCT / ARCHITECTURE / QUALITY / MVP /
  TEST_STRATEGY / README / AGENTS rewritten for Chinese; ADR 007 (Pinyin
  replaces furigana) and ADR 008 (compactor targets Chinese structure)
  written; 001-006 inherited with a note where they reference language
  specifics. Status: COMPLETE.
- **P6 — Verification.** `./verify` green; desktop (1440x900) and mobile
  (412x892) headless visual review of the real templates + real stylesheet
  with realistic card data: hero/Pinyin stack, tone colours, compactor
  (2 senses kept, 2nd dictionary hidden), sentence + sentence-Pinyin,
  collapsed 译文/详情, and a `#listening`-without-audio front falling back to
  the sentence front. Status: COMPLETE.
- **P7 — Release.** git init, first commit, `gh repo create`, push, tag,
  apkg asset. Status: COMPLETE.
- **P8 — apkg verification (ADR 009).** During P7 the export was
  *misdiagnosed* as broken: an apkg was inspected via its
  `collection.anki2` entry, which is a vestigial companion holding stock
  note types (Basic/Cloze/Image Occlusion) rather than the exported
  content, and that made a working export look like a Default-deck export.
  A hand-rolled apkg writer was written to replace it. Correction:
  `exportPackage` works; the writer was deleted; `export_apkg.py` now
  exports and then re-reads `collection.anki21` to assert the note type,
  deck, and card count, with `tests/test_apkg.py` pinning both the correct
  path and the five failure modes it must reject. Status: COMPLETE
  (superseded for the release artifact by U4 / ADR 011; the
  `collection.anki21` inspection lesson remains).

## Upstream sync (from anki-japanese-template, 2026-11-21)

The Japanese repo's language-agnostic work after the 2026-09-30 port was
imported in priority tiers. U1–U4 are COMPLETE; the notes below remain as
the record of what was taken, adapted, or deliberately dropped.

```text
U1 correctness + readability   ← COMPLETE
U2 layout/UX                   ← COMPLETE
U3 wide-card side rails        ← COMPLETE
U4 CI-built releases           ← COMPLETE
```

- **U1 — correctness + readability.** COMPLETE:
  - cloze: an already-contained trio is highlighted in place, never
    replaced by a fragment (Japanese `7e5f915` + `3ab46f7`); new
    `tests/test_cloze_fallback.py`.
  - image-only definitions/secondary content survive empty-collapse
    (`ece31e9`); `tests/test_back_more.py` cases 5–7, CSS
    `.is-media-only`.
  - readability floor: AA muted text, no hint/footer opacity, 12px
    chrome-label floor (`5c2016b`); new `tests/test_readability.py`.
  - test hygiene: `verify.yml` installs CJK fonts; `test_layout.py`
    refuses to measure tofu without a Chinese font and its stale Japanese
    fixtures (ruby sentence, `Z` hint, long-sentence replace target) are
    corrected.
- **U2 — layout/UX.** COMPLETE: bigger sentence type + mobile hierarchy
  (`770f0f7`); long-hero stacking (`a28dba2`); clickable shortcut hints
  (`1151d71`, `5ca387a`, `35bf568`, final state after `5c2016b`) — the hint
  bar is now buttons routed through `window.applyShortcut` (P/X/C), visible
  on phones as ≥44px touch targets, so `P` (hide Pinyin) works without a
  keyboard.
- **U3 — wide-card side rails.** COMPLETE (ADR 010; `ffb0cca` … `32bea79`):
  at `@container anki-card (min-width: 1000px)` the band leaves the flow and
  clips into two 6% full-height rails (one `{{Picture}}` per rail, both
  inside the one lightbox trigger); content moved into `.card-content`.
  Amends 006's single-Picture rule; keeps the Chinese warm accent (the
  Japanese cool-accent override was deliberately not ported). Phones and
  narrow panes keep the top band.
- **U4 — CI-built releases.** COMPLETE (ADR 011): `fetch_sample_deck.py`
  snapshots the live release deck into `samples/` (5 notes, 18 fields, 6
  media files); `build_sample_apkg.py` builds a deterministic legacy
  schema-11 apkg from repo files with stdlib only; `release.yml` runs
  `./verify`, builds, and publishes on a `v*` tag push; `finish.sh` stops
  at the tag push and never builds/uploads the asset. `export_apkg.py` and
  `tests/test_apkg.py` are retired. `./verify` runs
  `tests/test_sample_apkg.py` (36 checks) and `build_sample_apkg.py
  --check`. The 5 curated cards live in the release deck
  (`curate_release_cards.py --count 5 --replace`); the study deck is never
  part of the artifact.

## Roadmap (evolution loop input, not committed scope)

- R1: replace the hand-authored compactor fixtures with a real captured
  Yomitan Simplified `Definition` (blocks nothing today, but it is the only
  unverified part of the compactor).
- R2: retune frequency tiers once real Chinese `Frequency` values exist.
- R3: add structured-Chinese sense wrappers to §6b if such a dictionary is
  ever installed — fixture first, then CSS, then the JS mirror.
- R4: Traditional Chinese / Cantonese would need a decision of their own
  (script-aware font stack, possibly a `Traditional` variant field).

## State updates

Mark a task COMPLETE only after targeted checks + `./verify` + (for
template/CSS changes) the `finish.sh` release run. Update technical docs
only when something actually changed — no churn.
