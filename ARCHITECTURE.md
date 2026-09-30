# ARCHITECTURE.md — authoritative technical structure

Covers *how the software is structured* for the `MVP.md` scope. Additional
documents are created only where they would otherwise make this file
unwieldy or where a domain needs an independently maintained contract. Current
extras: `docs/adr/` (decisions with lasting consequences); no separate
`DATA_MODEL.md` / `API_CONTRACTS.md` / `STATE_MODEL.md` — the project is too
small to justify them.

## System map

```text
Anki note fields (live in Anki UI, never in repo)
  │  Yomitan (Simplified Chinese dictionaries) mining
  ↓
Card 1 - Front.template.anki ──→ review front (sentence / word / listening)
Card 1 - Back.template.anki  ──→ review back (grid: hero + meaning + context)
Card 1 - Style.css           ──→ themes, layout, tones, compactor, truncator
  │  vanilla JS (scoped, DOM-reuse safe), no libraries
  ↓
Anki renderers: Desktop Qt6 WebEngine · AnkiDroid WebView
  │  live services at render time: AnkiConnect :8765 (desktop only)
  ↓
Tooling (stdlib-only): fetch_anki_fields.py · sync_to_anki.py ·
                       export_apkg.py · verify · finish.sh
                       bootstrap_chinese_model.py (one-shot, create-only)
                       set_field_descriptions.py (idempotent)
                       seed_sample_cards.py (one-shot, create-only)
```

## Components

### Front (`Card 1 - Front.template.anki`)

A pure retrieval surface: only the tested Chinese renders. HTML
conditionals pick the branch; a synchronous JS resolver finalizes the
listening decision (Policy B: usable audio required); async JS finalizes
Mature Word Mode:

```text
Definition / Extended definition? ──yes──→ sentence-display (zero audio)
        │ no
Frequency (legacy)? ──yes──→ sentence-display (zero audio)
        │ no
Sentence Audio? ──yes──→ listening-view (audio-only card)
        │ no
sentence-display fallback
        │
cloze fixup: Sentence has no <b> AND cloze trio complete?
        │ yes → prefix + <b>body</b> + suffix
        │
Mature check (desktop only; not listening, Expression non-empty,
              interval ≥ LONG_INTERVAL_DAYS=365)?
        │ yes → .word-mode: front-word-display only
        │ no  → sentence front (also the universal fallback)
```

The front is **language-independent**: none of the above mentions a
language. The Chinese delta versus the Japanese original is that
`Sentence (furigana)` has no successor — there is no Pinyin-bearing field
on the front at all, and a test enforces that ban.

Mature Word Mode is **desktop-only by design**: on Android/mobile the
template deliberately makes no interval request at all (no AnkiDroid JS
API call), because those calls can surface natively as false "Card Content
Error: Failed to load" media warnings in the reviewer. Mobile always keeps
the sentence front; reliability of the reviewer beats this optional
presentation feature.

Hidden behavioral probes never render visibly: the cloze trio and the
tags probe. Normal cards never evaluate `{{Sentence Audio}}` on the front,
guaranteeing zero audio autoplay and zero audio controls on normal cards.
**Listening Policy B**: `#listening` (or the legacy audio-only shape)
activates the listening front **only when usable audio exists**
(`hasUsableAudio` check on the `.raw-audio-source`). The tag-listening-view
binds to `{{Sentence Audio}}` (label 例句), falling back to `{{Word Audio}}`
(label 词语) — never the hardcoded `play:a:0`. `#listening` + no usable
audio falls back to the normal sentence front; dead/duplicate views are
removed so exactly one listening button is ever visible.
Interval retrieval is **desktop-only** via a single **content-search**
path (the live `guiCurrentCard` reviewer read was removed — reviewer and
Browse previewer now share the identical code path):
- Content search (only path): `findCards` by Expression, then Sentence
  and cloze-body discriminators narrow to exactly one candidate. **Never
  picks candidate 0**; if ambiguity remains, fails safely to the sentence
  front.
- Mobile: **no retrieval** — `post` UA-guards every AnkiConnect call
  before any fetch (refused localhost requests surface natively as false
  "Failed to load" media warnings); interval stays null → sentence front.
Anti-flash gate (`visibility:hidden` → reveal, 1200 ms safety cap); blank
sentence blocks are removed after the cloze fixup. The gate is
deterministic and safe: it never depends on a single async path or timer
that can be throttled. See `docs/adr/001-*`.

`:has()` is intentional architecture for empty-shell collapse (§6b, §10);
it is not removed for theoretical portability. Front template size is not
a defect — correctness is prioritized over line count.

### Back (`Card 1 - Back.template.anki`)

Single quiet column with typography-driven hierarchy:

```text
card-container
  ├── .scenic-band (photo-derived when Picture exists; aria-hidden
  │    ink-wash pagoda fallback otherwise; click/Enter opens the lightbox)
  ├── .hero-header (3-col grid: left meta | centered word | right meta;
  │    stacked word-over-sides on phones)
  │    ├── .hero-side-left (freq visualizer + 词语 audio)
  │    ├── .hero-word-wrap (column!)
  │    │    ├── .word-display (target — hero element)
  │    │    └── .pinyin-display (reading; tone-coloured)
  │    └── .hero-side-right (例句 audio)
  ├── definition-box.primary-definition (compacted §6b, 3-line §6c)
  ├── .context-grid (full-width sentence surface)
  │    ├── .sentence-chinese
  │    └── .sentence-pinyin (optional, quieter tier)
  ├── .more-section (hidden) + .more-toggle "详情 ▾"
  │    └── translation (click/T/X) · context · hanzi notes · notes · source
  │        (.source-footer) · full extended definition (.extended-full —
  │        compactor never touches it)
```

`.hero-word-wrap` is `flex-direction: column`: the headword and its Pinyin
line are one centered reading unit. Row direction would place them side
by side; a layout test pins this.

JS controllers (all idempotent under WebView DOM re-use): More toggle
(one-way reveal; section+button self-remove when secondary content is
absent), native-only circular audio (`playCircularAudio` → sibling replay
link click, re-tap debounce, playback indicator pulse), **Pinyin tone
colouring** (`applyPinyinTones` → `tone-0..4` spans), definition truncator
(blank boxes removed, then measure → `.is-truncated` → one-way
`.is-expanded`), lightbox (backdrop-click / `Escape` close, alt
preserved), back-only keyboard shortcuts (`P` Pinyin visibility, `T`/`X`
translation reveal, `C` expanded-info toggle; `R` is Anki-owned, never
listed).

#### Pinyin tone colouring (`applyPinyinTones`)

```text
input   "zhōng guó"            plain text, whitespace-separated syllables
tone    first marked vowel in  ā ē ī ō ū ǖ → 1 │ á é í ó ú ǘ → 2
        the syllable           ǎ ě ǐ ǒ ǔ ǚ → 3 │ à è ì ò ù ǜ → 4
        (numeric "zhong1" wins, trailing 0/5 → tone 0)
output  <span class="tone-N">zhōng</span> <span class="tone-2">guó</span>
```

Invariants: only `.pinyin-display` / `.sentence-pinyin` are touched; a
field that already contains element children is left **byte-identical**
(mined markup is never rewritten) — except the single `{{edit:}}`
wrapper (`[data-EFDRCfield]`), whose text is toned in place; `data-tones-applied` makes a second
pass a no-op under WebView DOM re-use; the original text is preserved
inside each span, so only wrapping happens. §9 owns the palette and the
`P` hide rule.

### Style (`Card 1 - Style.css`)

Numbered sections are the contract: §1 tokens/themes (Ink Night dark /
Rice Paper light, plus the `--tone-0..4` palette; no `--freq-*` reuse for
tones), §2 containers, §3 More toggle, §4 context grid + desktop
overrides, §5 front type, §5b word-mode swap, **§5c Pinyin line**,
§6 back hierarchy (hero-header 3-col grid: left meta | centered word |
right meta; stacked on narrow), **§6b Definition Compactor** (first
dictionary, ≤2 senses, no appendices, `.primary-definition`-scoped),
§6c truncator (3-line cap + fade + chevron), §7 audio rings (playback
indicator, not true progress), §8 sentence/translation + secondary blocks,
**§9 Pinyin tones + §9b Pinyin visibility toggle**, §10 media/lightbox,
§11 footer, §12 listening (inert until `.listening-mode`), §13 mobile,
§14 deletable ink-wash backdrop, §15 reduced motion (+ blur kill),
§16 card entrance (single 0.15s settle, no stagger; killed by §15),
§17 scenic band (photo mode with illustrated fallback).

`--furigana-headroom` survives as a **generic vertical clearance** token:
it is the §6c truncator's line-height math and the definition/sentence top
padding. It is no longer ruby clearance — nothing in the Chinese port
hides a reading above a line.

### Tooling

```text
fetch_anki_fields.py → .anki_fields.json (gitignored, read-only dump)
bootstrap_chinese_model.py → one-shot: createModel + createDeck (refuses to re-run)
set_field_descriptions.py  → idempotent: writes the Fields-dialog descriptions
sync_to_anki.py      → snapshot backups/<ts>/, push Front/Back/CSS
seed_sample_cards.py  → 3 sample notes so the deck (and the apkg) is non-empty
export_apkg.py         → exportPackage deck → dist/*.apkg, then RE-OPEN
                        the zip, read `collection.anki21`, and assert the
                        note type, deck and note count (hard gate;
                        ADR 009). Refuses to export an empty deck, which
                        would silently produce a package with no note type.
verify               → local quality gate (tests only, no side effects)
finish.sh            → verify → stamp → sync → export → commit → push main → release (--target main) → fetch tag
tests/               → test_compactor.py + test_templates.py
                         + test_front_modes.py + test_mature_content.py
                         + test_pinyin_tones.py + test_layout.py
                         + test_yukei.py + test_back_more.py
```

Fields are **not** a repo artifact: the Anki UI owns them; agents bootstrap
via `fetch_anki_fields.py` every session. `bootstrap_chinese_model.py` and
`set_field_descriptions.py` are the only scripts that mention field
names, and they are create/describe-only — never a source of truth.

## Diagrams

Produced only where prose is ambiguous. The front-mode decision graph and
the back tree above are the standing set; sequence/state/entity diagrams
are omitted — no complex async choreography, state machine, or persistent
entity graph exists beyond what is shown.

## Key decisions (summaries; full records in `docs/adr/`)

- **001** Mature interval via desktop-only content search (no
  `{{Interval}}`, no new fields/add-ons; `guiCurrentCard` live read
  removed after AnkiDroid false-media-warning debugging; mobile makes no
  network request at all and degrades to the sentence front).
- **002** Definition Compactor as structural CSS (dictionary-agnostic,
  `.primary-definition`-scoped; extended definition untouched).
- **003** Native-only audio delegation (no `new Audio()`; sibling replay
  link; debounce; visually-hidden-not-`display:none` source).
- **004** Single-command release (`finish.sh`; `verify` as the
  side-effect-free subset; snapshots before overwrite).
- **005** Compact scenic band on the back card, separate from the reading
  surface, with an animated illustrated fallback.
- **006** Cards with `Picture` use a CSS-treated photo in that same band
  and retire the separate context thumbnail; the existing lightbox is
  reused.
- **007** Pinyin replaces furigana: a separate plain-text field plus
  tone-coloured syllable spans, and a `P` visibility toggle in place of the
  `F` full-card furigana mode.
- **008** The compactor targets Chinese dictionary structure only; the
  Japanese structured-content sense selectors were removed rather than left
  as dead rules.
- **009** The exported apkg is verified by re-opening it and reading
  `collection.anki21`. `exportPackage` is correct, but an empty deck
  exports as a package containing no note type while returning success —
  and an apkg's `collection.anki2` is a vestigial companion that will
  mislead any inspection reading the wrong entry.

## Evolution rule

Small change → implement normally. Moderate change → update this file
(+ ADR when justified) first, then add tasks. Major change → stop feature
work, run an explicit architecture-change effort with a migration plan.
