# IMPLEMENTATION_PLAN.md — task graph + status

The graph is part of the plan (not a substitute): the graph says *what
depends on what*, the task entries say *what each node means*. This is a
task/slice graph, not a todo list (`Build frontend` would not qualify).

## Where this repo came from

`anki-chinese-template` is a **language port** of
[`anki-japanese-template`](https://github.com/mansourvery-hub/anki-japanese-template).
Tasks T1-T17 (the whole front/back/compactor/audioscape/release history) are
inherited and are COMPLETE by construction — the code came across. They are
listed here for provenance, not as work.

The **port** is a separate, short graph below. Only its nodes are open work.

## Port task graph (the only open work)

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
- **P7 — Release.** git init, first commit, `gh repo create`, push, tag
  `v0.1.0`, apkg asset. Status: COMPLETE.

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
