# 🎴 Chinese Anki Note Template (Ergonomic & Responsive)

A modern, ultra-compact Simplified Chinese sentence-mining note type for Anki.
Built for dense, information-efficient review on **Desktop (Arch Linux, Qt6)**
and **Mobile (AnkiDroid, small screens)**.

Ported from [`anki-japanese-template`](https://github.com/mansourvery-hub/anki-japanese-template):
the front-mode logic, audio delegation, lightbox, truncator, empty-field
collapse and Mature Word Mode are language-agnostic and came across
unchanged. The reading subsystem is not — see
[ADR 007](docs/adr/007-pinyin-replaces-furigana.md) and
[ADR 008](docs/adr/008-chinese-compactor-structure.md).

---

## ✨ Features

- **🌙 Dual themes** — Ink Night dark (default) and Rice Paper light,
  following Anki's Night Mode.
- **🔢 Minimal by design** — every visible element must justify its screen
  space. The front is a pure retrieval surface (just the Chinese, never the
  reading); the back is a quiet reading interface: target → Pinyin → meaning
  → context, with secondary info collapsed behind `详情 ▾`. Anki is the SRS —
  no badges, dashboards, or grading UI.
- **🔤 Tone-coloured Pinyin** — the reading sits under the headword as one
  always-visible line, each syllable coloured by its Mandarin tone
  (1-4, neutral = grey). No ruby, no hover reveal, nothing that shifts.
  <kbd>P</kbd> hides both Pinyin lines for a Chinese-only read. Colour is
  applied to the Pinyin only — the target word keeps the single accent colour.
- **📱 Fluid responsive layout** — `clamp()` sizing with no breakpoint jumps;
  a compact scenic band spans the card top on desktop and phones, with
  full-width sentence context below. Cards size to their content (no forced
  viewport fill).
- **🔊 Native audio** — `例句` / `词语` buttons delegate to Anki's replay link
  (never HTML5 audio), with re-tap debounce so audio can't overlap on
  AnkiDroid. The ring is a playback indicator (a decorative play-pulse), not
  true progress. <kbd>R</kbd> is Anki's own shortcut (native replay) — the
  template never adds it. Custom template shortcuts: <kbd>P</kbd> (Pinyin),
  <kbd>X</kbd> (translation), <kbd>C</kbd> (expanded-info).
- **👁️ On-demand secondary info** — <kbd>T</kbd>/<kbd>X</kbd> reveals the
  translation; `详情 ▾` exposes the full dictionary definition, extra
  context, hanzi notes and general notes. <kbd>C</kbd> toggles expanded-info.
  Quiet by default.
- **🖼️ Lightbox** — tap the scenic photo (or press <kbd>Enter</kbd>) for the
  full-quality original; closes on backdrop click or <kbd>Escape</kbd>.
- **🏷️ Behavioral tags** — tags drive card behavior (e.g. `#listening` forces
  the listening front) and are never rendered as decoration.

---

## 🃏 Front Card Modes

The front contains ONLY the thing being tested — the sentence itself is the
retrieval prompt, and the reading is never shown (it would hand over half the
answer).

| Situation | Front shows |
| :--- | :--- |
| Definition present | Sentence (or Expression if no Sentence) |
| No definitions, but `Frequency` set (legacy cards) | Usual sentence — never the audio button |
| No definitions, no Frequency, `Sentence Audio` set | Listening-mode audio button |
| Card tagged `#listening` | Listening-mode audio button — **only when usable audio exists** (Sentence Audio, or Word Audio fallback); without audio, falls back to the sentence front |
| Nothing available | Sentence / Expression fallback |
| Sentence has no bold term + cloze trio complete | Rebuilt `prefix + <b>body</b> + suffix`, styled identically to a Yomitan sentence |
| Review interval ≥ 365 days (desktop only) | Word only (Mature Word Mode, see below); Android keeps the sentence front |

**Cloze fallback** (some mobile mining exports): when `Sentence` lacks its
`<b>` target word, JS rebuilds it from `cloze-prefix` / `cloze-body` /
`cloze-suffix` — but only if all three are non-empty, otherwise the sentence
is kept as-is.

**Mature Word Mode** (anti-overlearning, desktop only): old cards stop testing
the word and start testing sentence recognition, so at
`interval ≥ LONG_INTERVAL_DAYS` (default `365`, one constant in
`Card 1 - Front.template.anki`) the front shows only the `Expression`. The
interval is resolved at render time via AnkiConnect **content search**
(`findCards` by Expression, then Sentence → cloze-body discriminators —
reviewer and Browse previewer share the one identical fallback-only path).
On Android/mobile this mode is **intentionally disabled** and the ordinary
sentence front is shown: the `post` helper UA-guards every AnkiConnect call
before any fetch, because refused localhost requests can surface natively as
false "Card Content Error: Failed to load" media warnings in the reviewer. The
search **never picks candidate 0** blindly; if ambiguity remains, it fails
safely to the sentence front. Any failure degrades to the normal sentence
front; listening cards are never touched; an anti-flash gate keeps the card
hidden until the decision is made (500 ms fetch timeout, 1200 ms reveal cap).

**Listening semantics (Policy B)**: the audio button markup is gated on
`Sentence Audio` and inert until a synchronous resolver confirms the listening
condition — the classic audio-only field shape OR the `#listening` tag —
**with usable audio**. The tag-listening-view binds to the actual
`{{Sentence Audio}}` field (not the hardcoded `play:a:0` which plays the first
audio field = Word Audio); Word Audio is the fallback, and the label matches
what plays (例句 for sentence, 词语 for word). `#listening` + no usable audio
falls back to the normal sentence front. The resolver removes every
dead/duplicate view so exactly one listening sound button is ever visible.

---

## 📖 Back Card

Typography does the work — no dashboard chrome:

1. **Scenic band** — the card's `Picture` rendered as a compact CSS-treated
   photo, or an animated ink-wash mountain fallback when empty. Photo cards
   open the full-quality original in the lightbox.
2. **Target + Pinyin** — the headword is the hero element, with its Pinyin
   line directly beneath it. Tone colours come from `applyPinyinTones()`,
   which reads the diacritics (or a trailing digit) of the plain `Pinyin`
   field; a syllable with no detectable tone renders neutral, and a field
   containing markup is left untouched.
3. **Primary meaning** — **Definition Compactor** (CSS §6b) trims the mined
   glossary to the first dictionary, max 2 senses, no appendices;
   **Definition Truncator** (§6c) caps it at 3 lines with a fade + `▼`, click
   expands and stays open.
4. **Context** — the sentence spans the full reading width, with the optional
   `Sentence Pinyin` as a quieter second line.
5. **Secondary info** — collapsed behind a quiet `详情 ▾`: translation
   (`T`), additional context, hanzi notes, general notes, source, and the
   **full extended definition** (the compactor never touches it).

---

## 🗂️ Fields

Fields are managed **exclusively inside the Anki UI** — the repo keeps no
static list. For the live names + descriptions, run:

```bash
python3 fetch_anki_fields.py   # dumps gitignored .anki_fields.json
```

The note type ships with 18 fields: `Expression`, `Definition`,
`Hanzi Notes`, `Source`, `Sentence`, `Sentence Pinyin`, `Sentence Audio`,
`Translation`, `Picture`, `context`, `Notes`, `Word Audio`, `Pinyin`,
`cloze-prefix`, `cloze-body`, `cloze-suffix`, `Frequency`,
`Extended definition`. Yomitan-mining compatible.

Relative to the Japanese original, `furigana` and `reading` are replaced by a
single `Pinyin`, `Sentence (furigana)` becomes `Sentence Pinyin`,
`Kanji Notes` becomes `Hanzi Notes`, and `Pitch Accent` is dropped (tones live
in the Pinyin line now).

---

## 🚀 Installation

**Option 1 — Quick install (recommended):** download
`anki-chinese-template.apkg` from
[Releases](https://github.com/mansourvery-hub/anki-chinese-template/releases),
import via **File → Import**, then delete the sample cards (the note type is
retained).

**Option 2 — Sync from source** (needs Anki +
[Anki-Connect](https://ankiweb.net/shared/info/2055492159), Python 3 stdlib
only):

```bash
git clone https://github.com/mansourvery-hub/anki-chinese-template.git
cd anki-chinese-template
python3 sync_to_anki.py    # snapshots live state to backups/, then pushes Front/Back/CSS
python3 build_apkg.py       # builds + verifies dist/*.apkg from the deck
```

The note type and deck must exist first. One-shot, create-only:

```bash
python3 bootstrap_chinese_model.py   # creates the model + "My Life Decks::Chinese"
python3 set_field_descriptions.py    # idempotent: writes the Fields-dialog text
python3 seed_sample_cards.py         # 3 sample notes (see below)
```

The deck ships 3 sample notes, tagged `anki-chinese-template-sample`. They
exist because Anki's exporter degrades to the Default deck when the target
deck is empty, and because a fresh install should be a smoke test of the
front modes, the compactor, Pinyin tones and the listening front. Delete
them any time — the note type and deck survive.

> **`build_apkg.py` does not use Anki's exporter.** The installed
> Anki-Connect is built for Anki 25.x and runs on Anki 26.09.3, where its
> `exportPackage` silently returns success while exporting the **Default**
> deck. `build_apkg.py` therefore writes the package itself and then
> re-opens it to assert the note type, deck, and note count — a mismatch
> aborts `finish.sh` before anything is published. See
> [ADR 009](docs/adr/009-build-apkg-in-repo.md).

**Option 3 — Manual:** paste `Card 1 - Front.template.anki`,
`Card 1 - Back.template.anki`, and `Card 1 - Style.css` into the card template
editor (**Tools → Manage Note Types → Cards**).

---

## 🛠️ Project Structure

```
├── Card 1 - Front.template.anki   # Front HTML: modes, cloze fallback, Mature Word Mode
├── Card 1 - Back.template.anki    # Back HTML: hero, Pinyin, definition, sentence, More
├── Card 1 - Style.css             # Themes, layout, scenic band (§17), tones (§9), compactor, truncator
├── fetch_anki_fields.py           # Read-only dump of live Anki fields (see above)
├── bootstrap_chinese_model.py     # One-shot: create the note type + deck (refuses to re-run)
├── set_field_descriptions.py      # Idempotent: writes the field descriptions
├── sync_to_anki.py                # Push templates/CSS to Anki (pre-sync backup)
├── build_apkg.py                  # Build + verify dist/*.apkg (see ADR 009)
├── seed_sample_cards.py           # One-shot: 3 sample notes so the deck exports
├── verify                         # Local quality gate (tests only, no side effects)
├── finish.sh                      # One command: verify + sync + export + commit + push + release
├── PRODUCT.md / MVP.md            # Product intent / current scope
├── ARCHITECTURE.md + docs/adr/    # Technical structure / lasting decisions
├── QUALITY.md / TEST_STRATEGY.md  # Invariants / how they are verified
├── IMPLEMENTATION_PLAN.md         # Task graph + status
├── tests/                         # Compactor, templates, front modes, mature search, Pinyin tones, layout, scenic band, back More (run by ./verify)
├── chat_history/                  # Archived agent prompts
├── dist/                          # Exported .apkg (gitignored, GitHub Release asset)
├── backups/                       # Pre-sync Anki snapshots (gitignored)
├── AGENTS.md                      # Agent operating rules
└── README.md                      # This file
```

---

## 🔄 Development Workflow

Edit the local `.template.anki` / `.css` files (never inside Anki's UI), then
run one command:

```bash
./finish.sh "scope: what changed"
# --local: sync + export + commit only · --minor: bump v0.x.0 · --prompt "text": archive prompt
```

This runs tests, syncs to Anki, builds and **verifies** the apkg, commits,
pushes, and publishes a tagged release.

`tests/` covers the compactor selectors and their JS mirror, template
invariants (reading ban on the front, audio/lightbox semantics, balanced
conditionals, listening Policy B, R-is-Anki-owned, P/X/C shortcuts, Chinese UI
strings), the Pinyin tone controller, front-mode resolver behavior, mature
content-search fallback (duplicate cards / ambiguity), scenic-band
photo/fallback consolidation, back-More lazy loading, and headless layout
checks.

---

## ⚠️ Known gaps

- Compactor fixtures are hand-authored from documented CC-CEDICT /
  structured-dictionary shapes, **not** captured from a real Yomitan
  Simplified mine. Replace them with a real capture on the first mined card.
- Frequency tier thresholds (500 / 2.5k / 7k / 18k) are inherited from the
  Japanese original and are expected to be wrong for Chinese.
- Mature Word Mode is desktop-only by design (AnkiConnect); mobile always
  keeps the sentence front.

---

MIT License.
