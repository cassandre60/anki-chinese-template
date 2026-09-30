# 008 — Compactor targets Chinese dictionary structure, not Japanese SC markup

Status: accepted · Date: 2026-09-30

## Context

The Definition Compactor (§6b) is a set of `display:none` rules plus a
1:1 live-DOM twin in `pruneCompactedGlossary()`. The Japanese original
matched two selector families:

1. **Structural**: `.yomitan-glossary > ol > li` (one `<li>` per
   dictionary), `[data-sc-content="glossary"] > li` (gloss list),
   `[data-sc-content="forms"]`, `[data-sc-content="attribution"]`, `i`
   (dictionary labels).
2. **Japanese structured-content sense wrappers**:
   `div[data-sc-name="語義G"]`, `div[data-sc-l3]`, `div[data-sc-l3-a"]`,
   `div[data-sc-name="補説G"]`, `span[data-sc-name="可能形"]`,
   `span[data-sc-name="歴史仮名"]`, `span[data-sc-name="アクセントG"]`.

Family 2 exists because 大辞林/大辞泉-style structured dictionaries wrap
each sense in a named `<div>`. **No Simplified Chinese dictionary in Yomitan
emits that markup.** CC-CEDICT and friends are flat: one `<li>` per
dictionary, senses as a plain `<li>` gloss list.

Keeping family 2 would be ~7 selectors that match nothing on every real
card — dead weight that also pretends to constrain markup this language
never produces, and that a future editor would assume is load-bearing.

## Decision

**Keep family 1, delete family 2**, and extend family 1 where the Chinese
markup legitimately differs:

- A `<ul>`-per-entry variant is now also constrained
  (`.yomitan-glossary > ul > li ~ li`), because dictionary authors
  disagree on `<ol>` vs `<ul>` for the per-dictionary list.
- Sense lists are constrained in both shapes
  (`[data-sc-content="glossary"] > li ~ li ~ li` and the `> ul > li`
  variant), because CC-CEDICT puts glosses directly under the content
  element while structured dictionaries nest them one level deeper.
- `[data-sc-content="forms"]` is matched on the element itself rather than
  on `li` only, for the same reason: the attribute sits on either the
  `<li>` or its wrapping `<ul>` depending on the dictionary.
- Same for attribution: both `div` and `span` carriers.

The keep counts are unchanged (1 dictionary, ≤2 senses) and the CSS/JS
mirror contract is unchanged: every rule in §6b has a matching
`dropFrom`/`.remove()` call in `pruneCompactedGlossary()`, and
`tests/test_compactor.py` enforces the mirror on fixtures plus a scope
guard that every hide selector is `.primary-definition`-prefixed.

## Consequences

- The fixtures are now `yomitan_chinese_gloss.html` and
  `yomitan_chinese_structured.html`; the Japanese fixtures were removed
  because they no longer describe anything this template renders, and
  keeping them would have let the suite pass on markup that cannot occur.
- **The fixtures are hand-authored, not captured from a real mine.** They
  encode the structural shapes CC-CEDICT and structured dictionaries are
  documented to produce. The first real Yomitan Simplified mine is the
  moment this decision gets field-verified — if the real `Definition`
  HTML differs, the fixture must be replaced with the real capture before
  the compactor can be called correct.
- Adding a structured Chinese dictionary later means teaching §6b its
  sense-wrapper shape first (fixture, then CSS, then the JS twin). The
  order matters: CSS without the twin leaves hidden nodes costing layout;
  the twin without the CSS changes nothing visible.
