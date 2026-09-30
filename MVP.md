# MVP.md — current scope

`PRODUCT.md` answers *what is this product?* This file answers *what are we
actually building right now?* Agents must not independently widen this scope
while coding.

## MVP goal

A shippable, review-ready Chinese sentence-mining note type: dense on
desktop, usable on a small phone, with sentence/word/listening fronts, a
compact informative back with tone-coloured Pinyin, and a one-command
sync → export → release loop.

## Core user journey(s)

1. Import the release `.apkg` → review mined cards daily on desktop and phone.
2. Mature cards automatically test the word, not the memorized sentence.
3. Edit templates/CSS locally → `./finish.sh` → cards updated in Anki and a
   new tagged release published.

## Included capabilities

- Front: pure retrieval surface — sentence / Expression fallback,
  Frequency-legacy sentence path, cloze-trio rebuild, pure audio-only
  listening cards (usable audio required; `#listening` without audio falls
  back to sentence), Mature Word Mode (interval-gated, desktop-only
  AnkiConnect content search — one fallback-only path for reviewer and
  Browse previewer, mobile intentionally degrades to the sentence front,
  never picks candidate 0, sentence fallback). **No reading-bearing field
  exists on the front.**
- Back: typography-driven hierarchy — compact scenic band (photo when
  `Picture` exists, ink-wash illustrated fallback otherwise), word target
  with an always-visible Pinyin line, four-tone colouring, quiet
  frequency visualizer, Definition Compactor (CSS §6b, Chinese structural
  markup), 3-line truncator with one-way expand (§6c), full-width sentence
  context with an optional sentence-Pinyin line, native circular audio
  (playback indicator, not true progress), secondary information collapsed
  behind `详情 ▾` (translation, context, hanzi notes, notes, full extended
  definition), source footer. Custom shortcuts: `P` Pinyin, `X`/`T`
  translation, `C` expanded-info; `R` is Anki-owned (never in the
  template's shortcut UI). All strings Chinese.
- Styling: Ink Night + Rice Paper themes, fluid clamps, compact scenic
  band with CSS-only photo treatment, tone palette, reduced-motion
  support, CJK font stack with a tone-mark-safe Latin stack.
- Empty-field collapse everywhere: no padding, border, or margin survives an
  empty field; the More section and its toggle self-remove when empty.
- Tooling: field bootstrap (`fetch_anki_fields.py`), one-shot model/deck
  creation (`bootstrap_chinese_model.py`), idempotent field descriptions
  (`set_field_descriptions.py`), snapshotted sync (`sync_to_anki.py`),
  apkg export (`release_apkg.py`), `verify` gate, `finish.sh` release loop,
  regression tests (compactor + templates + front-modes + mature-content +
  Pinyin tones + layout + scenic-band + back-More contracts).

## Excluded capabilities

- New fields, add-ons, or review-time Python.
- Additional card types or note types.
- Traditional Chinese, Cantonese, Wade-Giles.
- Cloud sync / collaboration / analytics.
- Mandatory per-project doc/diagram checklists beyond `ARCHITECTURE.md`.

## Acceptance criteria

- `./verify` passes (compactor + template invariants + Pinyin tone
  controller; layout checks when Chrome is present).
- A real user can complete: import → review sentence card → review mature
  word card → review listening card → expand definition/translation/image →
  hide Pinyin with `P` → edit locally → `./finish.sh` → updated cards +
  tagged release.
- No horizontal overflow, no viewport-fill dead space, the Pinyin line never
  displaces the target, audio never overlaps, failures always degrade to the
  sentence front.

## Known limitations

- Mature interval needs AnkiConnect (desktop); Browse/template previews
  without it correctly fall back to the sentence front.
- Mature Word Mode is **intentionally unavailable on Android/mobile** (safe
  sentence fallback). The template makes no AnkiDroid JS API interval request,
  because those calls can surface natively as false "Card Content Error:
  Failed to load" media warnings in the reviewer.
- Headless layout checks skip gracefully when Chrome is absent.
- Compactor fixtures are hand-authored from documented CC-CEDICT /
  structured-dictionary shapes, **not** captured from a real mine (ADR 008).
- Frequency tier thresholds are the Japanese ones and are expected to be
  wrong for Chinese.

## Deferred features

- Retune frequency tiers once real Chinese `Frequency` values are observed.
- Capture a real Yomitan Simplified `Definition` as the fixture baseline,
  then field-verify the compactor.
- Add structured-Chinese sense wrappers to §6b if a structured Chinese
  dictionary is ever installed.
- A reliable mobile interval source that does not trigger AnkiDroid's false
  media-load error (revisit if AnkiDroid stabilises its JS API).
- Any `docs/adr/` entries beyond decided items (added only when a decision
  has alternatives + consequences + long-term relevance).
