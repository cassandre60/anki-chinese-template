# 007 — Pinyin replaces furigana

Status: accepted · Date: 2026-09-30

## Context

The template is a port of `anki-japanese-template`, whose reading
subsystem is built around **furigana**: a `furigana` field rendered
through the `{{furigana:…}}` filter into `<ruby>` markup, hidden `rt`
elements revealed on hover/tap, absolute positioning plus a reserved
`--furigana-headroom` band so the reveal causes zero reflow, and an `F`
shortcut that pins every `rt` on the card at once.

Chinese has no ruby. Yomitan's Simplified Chinese dictionaries do not emit
`<ruby>`, do not carry a reading field in the same shape, and Mandarin tone
is information the Japanese card has no analogue for at all.

Three options were considered:

1. **Keep the ruby machinery and feed it Pinyin.** Per-syllable ruby over
   Hanzi is what Pinyin converters emit (`漢<rt>hàn</rt>`), but it is
   visually wrong for Chinese learners — it re-encodes one syllable per
   character, which is only true for monosyllabic words — and it
   multiplies the per-card DOM by ~2-3x on text that is already
   character-dense. A two-syllable word like 窗户 became 窗<rt>chuāng</rt>
   户<rt>hu</rt>, which teaches the wrong thing.
2. **A separate plain `Pinyin` field rendered as one line under the
   headword**, optionally tone-coloured.
3. **No reading at all** (drop furigana's replacement entirely).

Option 3 fails the product: the learning task is *Chinese word → Pinyin +
meaning*, so removing the reading removes the answer.

## Decision

**Option 2.**

- `Pinyin` (headword reading) and `Sentence Pinyin` are plain-text
  fields. No `{{furigana:}}` filter, no `<ruby>`, no `rt`.
- The reading is **always visible** on the back card. Furigana was
  hidden-until-hover because the target word was already large and the
  reading duplicated it; Pinyin is the *only* place the reading exists, so
  hiding it would hide a third of the answer. The `F` full-card furigana
  mode has no successor because there is nothing left to pin — the one
  remaining reveal, `P`, *hides* the Pinyin lines instead.
- **Tone colouring** is the new feature that replaces the pitch-accent
  line the Japanese card had. `applyPinyinTones()` wraps each whitespace-
  separated syllable in `tone-0..4` from its vowel diacritics (or a
  trailing digit, where `0` and `5` fold onto neutral).
- Colour is applied to the **Pinyin only**, never to the Hanzi. The target
  word owns the single accent colour; giving each character its own hue
  would make the answer look like a rainbow and destroy the target
  highlight that marks the retrieval cue.
- Front: no Pinyin-bearing field exists on the front at all, so the
  reading can never leak onto the retrieval surface. This is enforced by a
  test, mirroring the old "no furigana on the front" invariant.

## Consequences

- §9/§9b of the stylesheet were repurposed rather than deleted: the
  `--tone-*` palette and the `P` toggle replace the `ruby rt` rules. The
  section numbers are contracts referenced by tests and docs, so they
  stayed.
- `--furigana-headroom` is kept as a generic vertical-clearance token
  because §6c's 3-line truncator math is expressed in terms of it. It no
  longer reserves ruby space; the scenic band's 12px tuck under
  `.word-display` is now expressed as an explicit 12px padding.
- Tone detection is a heuristic over text, so it can mis-colour an unusual
  syllable (erhua, a foreign proper noun). Failure is cosmetic only: a
  wrong tone is a wrong hue, never wrong text, and an undetectable
  syllable renders as `tone-0`.
- If the learner later mines Traditional Chinese or Cantonese, this
  decision needs revisiting — the diacritic table is Mandarin-specific.
