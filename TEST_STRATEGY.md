# TEST_STRATEGY.md — how QUALITY.md is mechanically verified

```text
QUALITY.md (WHAT must remain true)
  → TEST_STRATEGY.md (HOW it is verified)
    → tests / linters / headless checks / CI
```

## Layers (narrow → broad)

```text
tiny brick test → targeted suite → ./verify → CI (clean env)
```

While iterating, run the targeted suite; before declaring a task complete,
run `./verify`; CI re-runs `./verify` after every push.

## Enforcement map

| Requirement (QUALITY.md) | Enforcement |
| --- | --- |
| Compactor keeps 1st dictionary, ≤2 senses, no appendices; extended definition untouched; rules scoped to `.primary-definition`; no Japanese SC selectors; JS prune mirrors the CSS 1:1 | `tests/test_compactor.py` — extracts the real `display:none` rules from CSS §6b, applies them to `tests/fixtures/*.html` (bs4 + soupsieve), and diffs against a hand-mirrored `apply_prune()` |
| Front reading ban (no `Pinyin` / `Sentence Pinyin`); raw Sentence/Expression present | `tests/test_templates.py` §1 |
| Audio aria-labels; native-only controller; sibling replay source; debounce; restart-only | `tests/test_templates.py` §§2–3b |
| Cloze probe shape, trio gate, `<b>` rebuild, bold guard | `tests/test_templates.py` §2c |
| Scenic band: one `Picture` reference; photo/fallback conditionals; accessible photo trigger; no retired inline thumbnail; corrected `saturate()` + `overlay` pipeline; fallback reduced motion | `tests/test_yukei.py` — back-template/CSS structural contracts plus headless Chrome interaction/layout probes |
| Lightbox backdrop-only close, dialog semantics, alt | `tests/test_templates.py` §4 |
| Balanced Anki conditionals | `tests/test_templates.py` §5 |
| More collapse; P/X/C shortcuts (never R); listening resolver wiring; all UI strings Chinese | `tests/test_templates.py` §§6b–6e |
| Pinyin line: separate field, no ruby, `P` toggle hides both lines with `display:none` | `tests/test_templates.py` §6b (new) |
| Pinyin tone colouring: controller + table present, all five `--tone-*` classes styled | `tests/test_templates.py` §6b (new) |
| `:focus-visible`, reduced motion, content-driven sizing, context-grid fallback, clamp() authority, no JS font override | `tests/test_templates.py` §§6–7 |
| Mature Word Mode: const, desktop-only retrieval, no executable AnkiDroid JS API / bridge code, mobile degrades to sentence, no `note:` clause, anti-flash gate, word-mode CSS | `tests/test_templates.py` §8b |
| Mature content-search fallback: never picks candidate 0, Sentence + cloze-body discriminators, fails safely on ambiguity, exact-card resolution | `tests/test_mature_content.py` — extracts the content-search block verbatim, runs 6 headless Chrome cases with mocked AnkiConnect (skipped gracefully without Chrome) |
| Listening Policy B + exactly-one-button | `tests/test_front_modes.py` — 8 state harnesses in headless Chrome (skipped gracefully without Chrome) |
| Listening audio source: tag-listening-view binds to `{{Sentence Audio}}` (not `play:a:0`), Word Audio fallback, label matches (例句 / 词语) | `tests/test_templates.py` §6d |
| Tone colours: diacritic + numeric detection, ü variants, neutral folding, markup never rewritten, idempotence, `P` toggle preserves spans | `tests/test_pinyin_tones.py` — extracts `applyPinyinTones` + `PINYIN_TONE_MARKS` verbatim and runs 16 headless Chrome assertions (skipped gracefully without Chrome) |
| finish.sh deterministic ordering (push main before release, `--target main`), no-op protection | `tests/test_templates.py` §9 |
| Stdlib-only sync, microsecond backups | `tests/test_templates.py` §9 |
| Content-driven height, no h-overflow, Pinyin stacked **under** the headword and inside its cell, type hierarchy, 3-line clamp + one-way expand, listening target size, context grid, More collapsed by default, footer containment | `tests/test_layout.py` — headless Chrome on the **real** stylesheet; skipped gracefully when Chrome is absent |
| Back More lazy-load (template stays inert until first open, stamped once) + prune shrinks the live DOM | `tests/test_back_more.py` — extracts the real `toggleMore` / `initSecondarySection` / `pruneCompactedGlossary` and runs them in headless Chrome (skipped gracefully without Chrome) |
| Release asset carries OUR note type, deck, and every note; the gate can fail | `tests/test_apkg.py` — builds a package from synthetic data and re-opens it; also asserts `verify_apkg` **rejects** a wrong model name / wrong note count and says why (ADR 009) |
| Clean-environment pass, no forgotten files/deps | CI (`.github/workflows/verify.yml`) runs `./verify` |
| Every UI element collapses when its field is empty | `tests/test_templates.py` §10 — conditional-enclosure parser over Front/Back, `:has()` shell-guard checks, JS self-removal checks |

## The gate

`./verify` = the repository's complete mandatory **local** quality gate.
Side-effect free: it never touches Anki, never writes releases, never
commits. `finish.sh` step 0 delegates to it, so the gate and the release
pipeline can never disagree.

## Regression rule (inside the dev loop, not a separate phase)

```text
bug → diagnose → fix → add regression test → verify → commit
```

Every escaped bug earns a permanent test: compactor regressions → new
fixture/assertion; template/CSS regressions → a new `test_templates.py`
check; tone regressions → a new `test_pinyin_tones.py` assertion; layout
regressions → new `test_layout.py` probe assertion.

Two rules exist specifically because the Chinese port had to rebuild
scaffolding that the Japanese repo already had:

- **The compactor fixture must be a real capture.** The shipped fixtures
  are hand-authored from documented CC-CEDICT / structured-dictionary
  shapes (ADR 008). The first real mine replaces them; a fixture that was
  never observed is a hypothesis, not evidence.
- **A new tone case goes in `test_pinyin_tones.py`, not in a comment.**
  The diacritic table is a heuristic over arbitrary text; every new
  syllable shape that surprises it is a new assertion.

## Dependencies

- `test_compactor.py`: `beautifulsoup4` + `soupsieve` (test-only).
- `test_templates.py`: stdlib only (node optional for JS syntax checks).
- `test_front_modes.py`: headless Chrome if present, else skip (pass).
- `test_mature_content.py`: headless Chrome if present, else skip (pass).
- `test_pinyin_tones.py`: headless Chrome if present, else skip (pass).
- `test_layout.py`: headless Chrome if present, else skip (pass).
- `test_back_more.py`: headless Chrome if present, else skip (pass).
- `test_yukei.py`: stdlib only; headless Chrome optional for browser probes.
- `test_apkg.py`: stdlib only (no Anki needed — exercises `build_apkg.py`'s
  pure parts with synthetic data).
