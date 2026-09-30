# QUALITY.md — properties that must remain true

Answers *what must remain true*. `TEST_STRATEGY.md` answers *how it is
mechanically verified*. Code implements; tests enforce.

## Architecture invariants

- Local `.template.anki` / `.css` files are the single source of truth;
  never instruct edits inside the Anki UI.
- Fields live in the Anki UI only; the repo keeps no static field list.
  `bootstrap_chinese_model.py` and `set_field_descriptions.py` may name
  fields (create/describe only) but are never a source of truth.
- Vanilla JS/CSS only, scoped, DOM-reuse safe (idempotent init, no globals
  beyond the documented `window.*` controllers).
- Single `LONG_INTERVAL_DAYS = 365` const; no hard-coded `>= 365` elsewhere.
- CSS section numbers (§5c Pinyin, §6b compactor, §6c truncator, §9 tones,
  §9b Pinyin toggle, §14 backdrop) are stable contracts referenced by
  tests and docs.

## Front invariants

- Front renders **no** reading-bearing field: no `Pinyin`, no
  `Sentence Pinyin`, no `furigana`-style filter. Raw
  `{{edit:Sentence}}` / `{{edit:Expression}}` only. A reading on the front
  would hand over half the answer.
- Front shows **no UI** beyond the tested Chinese: no tags, badges,
  metadata, labels, or controls (hidden behavioral probes only: cloze trio).
  Normal cards NEVER render or play audio on the front.
- `R` shortcut is **Anki-owned** (native replay); the template never adds
  or modifies an `R` shortcut. Custom template shortcuts are `P`
  (Pinyin visibility), `X`/`T` (translation), `C` (expanded-info) — never
  `R`.
- Balanced `{{#field}}` / `{{^field}}` / `{{/field}}` conditionals.
- The sentence front is the **universal fallback**: every pathological /
  mature failure path degrades to it, never to a blank or hung card.
- Pure listening cards: `listening-view` renders only under
  `{{^Definition}}{{^Extended definition}}{{^Frequency}}{{#Sentence Audio}}`.
  Normal study cards never include `{{Sentence Audio}}` on front, guaranteeing
  zero audio autoplay on front.
- **Listening Policy B**: `#listening` activates the listening front **only
  when usable audio exists** (the tag-listening-view must have a real
  `.raw-audio-source` — `{{Sentence Audio}}`, or `{{Word Audio}}` as
  fallback). `#listening` + no usable audio falls back safely to the normal
  sentence front. The resolver removes every dead/duplicate listening view
  so exactly one listening sound button is ever visible.
- **Listening audio source**: the tag-listening-view binds to the actual
  `{{Sentence Audio}}` field (not the hardcoded `play:a:0` which plays the
  first audio field = Word Audio on listening cards). Word Audio is the
  fallback when Sentence Audio is absent. The label matches what plays
  (例句 for sentence audio, 词语 for word audio).
- Listening cards never enter Mature Word Mode and skip all interval
  retrieval.
- Interval has no `{{Interval}}` marker and no `note:` search clause
  (`{{Type}}` is the scheduling type, not the model): desktop uses
  AnkiConnect only; the mobile path makes **no interval request at all** —
  the AnkiDroid JS API is deliberately never called (it can trigger false
  "Card Content Error: Failed to load" media warnings), and mobile never
  fetches `127.0.0.1:8765`.
- **Mature mode interval retrieval** is desktop-only fallback content
  search (`findCards` by Expression → Sentence/cloze-body discriminators →
  `cardsInfo`). The live reviewer read (`guiCurrentCard`) was REMOVED —
  one identical path for reviewer and Browse previewer. Android/mobile
  intentionally degrades to the sentence front (`post` UA-guards every
  AnkiConnect call before any fetch); if ambiguity remains, retrieval
  fails safely to the sentence front. It never picks candidate 0
  blindly.
- Any retrieval failure degrades to the sentence front; anti-flash
  `visibility:hidden` gate with a bounded reveal cap. The gate is
  deterministic and safe: it must never depend on a single async path or
  timer that can be throttled, and it must never leave a blank/hung card.
- Cloze rebuild fires only when Sentence lacks `<b>`/`<strong>` **and** the
  full prefix/body/suffix trio is non-empty; rebuild uses `<b>`.
- The template contains **no executable AnkiDroid JS API code** and makes no
  `/jsapi/` request; mobile Mature Word Mode is intentionally disabled and
  degrades to the sentence front.
- `:has()` is intentional architecture for empty-shell collapse; it is not
  removed for theoretical portability.
- Front template size is not a defect; correctness is prioritized over line
  count. The front is not aggressively split/refactored.

## Back invariants

- Back hierarchy is typography-driven: compact scenic band → word-display
  (largest) + Pinyin line → metadata (5-star frequency visualizer &
  audio) → primary meaning → context → secondary collapsed behind 详情.
  Features discoverable via shortcut hints.
- **Pinyin line**: rendered from the plain `Pinyin` field, always visible,
  one line directly under the headword. No `<ruby>`, no `rt`, no hover
  reveal, no `{{furigana:}}` filter anywhere in the templates.
- **Tone colouring** (`applyPinyinTones`): wraps whitespace-separated
  syllables of `.pinyin-display` / `.sentence-pinyin` in `tone-0..4`;
  trailing digits `0`/`5` fold onto neutral; a field containing element
  children is left byte-identical; the original text is preserved inside
  each span; `data-tones-applied` makes a second pass a no-op. All five
  classes have a `--tone-*` rule, so an emitted class is never unstyled.
- **Tone colour never touches Hanzi** — only Pinyin spans. The target word
  keeps the single accent colour.
- `P` toggles `.pinyin-hidden` on the back wrapper, hiding both Pinyin
  lines with `display:none` (not opacity) so a hidden reading stops
  costing vertical space.
- `Picture` is referenced exactly once in the back template. A populated field
  renders the card-derived scenic photo and keeps click/Enter lightbox access;
  an empty field renders the non-focusable, `aria-hidden` illustrated fallback.
  The retired `.context-picture` markup is absent, so sentence context is
  full-width. The photo pipeline preserves source color with `saturate()` and
  `mix-blend-mode: overlay`; it must never use `grayscale()` +
  `mix-blend-mode: color`.
- Secondary information (translation, context, hanzi notes, notes, source,
  full extended definition) lives inside `.more-section`, toggleable via
  `详情 ▾` / `关闭 ▴`; the toggle and section self-remove when no secondary
  content exists.
- Content hierarchy communicates card mode directly: no retrieval-state
  badges, captions, or dashboard metadata.
- Keyboard shortcuts on the back: `P` toggles Pinyin visibility, `T` reveals
  the translation (opening More first), `X` toggles translation (alias for
  `T`), `C` toggles expanded-info; shortcuts never fire in
  inputs/contentEditable. **`R` is Anki-owned** (native replay) and never
  appears in the template's shortcut UI.
- Every circular audio button has an `aria-label`; replay source is a
  **sibling** `.raw-audio-source` (never inside `<button>`, never
  `display:none`); playback delegates to the native replay link; re-tap is
  debounced; `playCircularAudio` starts with `resetAudioState`; no `new
  Audio()`, no `is-paused` remnants, no `div`-inside-`button`. The ring is
  a **playback indicator** (a decorative play-pulse), not true progress —
  native audio remains the authority (ADR 003).
- Lightbox closes only on backdrop click (`e.target === overlay`) or
  `Escape`; overlay carries dialog semantics; cloned image preserves `alt`.
- Definition expand is one-way (never re-collapses); `.is-truncated` is set
  only on real overflow; no-JS still shows the full definition.
- No JS font-scaler overrides CSS (`.sentence-chinese` `clamp()` is the
  sizing authority).
- All user-visible strings are Chinese (`例句`/`词语` audio labels, `译文`
  translation hint, `详情`/`关闭` More toggle, `详细词典` extended header,
  frequency tier labels, aria-labels, shortcut hints).

## CSS invariants

- Compactor hide rules all scoped to `.primary-definition`; the full
  extended definition (`.extended-full` inside More) stays untouched.
- **No Japanese structured-content selectors** in the compactor
  (`語義G`, `data-sc-l3*`, `補説G`, `可能形`, `歴史仮名`, `アクセントG`):
  Simplified Chinese dictionaries emit no such markup (ADR 008).
- Word-mode swap rules exist and never touch `.listening-view`; the
  listening-view is inert until `.listening-mode` activates it.
- `.hero-word-wrap` is `flex-direction: column` so the headword stacks over
  its Pinyin line; row direction would break the centered reading.
- `--furigana-headroom` is used only as generic vertical clearance
  (definition/sentence top padding and the §6c line math); it is not ruby
  clearance and no rule hides a reading above a line.
- CJK font stack (`--font-chinese-serif` / `--font-chinese-sans`) and a
  separate Latin stack with tone-mark coverage (`--font-pinyin`) — Pinyin
  must never fall back to a font that renders ǚ/ǜ as tofu.
- Content-driven card height (no `100vh`/`100dvh` fill); `container-type:
  inline-size` present; the retained context-grid compatibility rules keep
  their media-query fallback.
- `:focus-visible` indicators and `prefers-reduced-motion` present.
- Accent color is reserved for target highlighting and interactive
  states; frequency indicator uses semantic tier colors (--freq-*); tone
  coloring uses the separate --tone-* palette.

## Empty-field collapse (space discipline)

- Every rendered field is enclosed in an Anki `{{#field}}` conditional —
  except the hidden cloze-probe trio, the hidden behavioral probes
  (`tags-probe`, field-presence markers), and the front word probe
  (`display:none` default, word-mode gate only).
- Unconditionally rendered shells collapse when all conditional children are
  absent: `.audio-row`, `.context-grid`, and `.context-main` via `:has()` guards;
  `.more-section` + `.more-toggle` self-remove via JS cleanup.
- Degenerate content removes itself instead of leaving chrome behind:
  blank definition/sentence blocks are removed (front runs after the cloze
  fixup, before the reveal); empty secondary blocks inside More are
  stripped.
- Net rule: no padding, border, or margin may survive an empty field.

## Tooling / process invariants

- Python tooling stays stdlib-only (test-only deps allowed); backups use
  microsecond timestamps; snapshots happen **before** any overwrite; empty
  live state aborts sync.
- `bootstrap_chinese_model.py` refuses to run when the model already
  exists — note-type creation is never a repeatable release step.
- `finish.sh` no-op runs never publish a release.
- Every user prompt is archived to `chat_history/opencode_prompts.txt`
  before/with the commit that follows it.

## Known-unverified

- Compactor fixtures are hand-authored, not captured from a real
  Simplified Chinese Yomitan mine (ADR 008). Field verification pending
  the first real card.
- Frequency tier thresholds are inherited from the Japanese original and
  are expected to be wrong for Chinese.
