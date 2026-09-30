#!/usr/bin/env python3
"""Definition Compactor regression tests.

Extracts the `display:none` rules from section 6b of the REAL
`Card 1 - Style.css` and applies them (simulated via DOM removal) to the
fixtures in tests/fixtures/. This catches:
  - CSS regressions (selector typos, accidental scoping changes)
  - Yomitan markup drift (fixture updates from real mined cards)

Run directly:  python3 tests/test_compactor.py
Also wired as finish.sh step 0 (auto-skipped when this file is absent).

Dependencies: beautifulsoup4 + soupsieve (pure Python, no Anki needed).
"""
import os
import re
import sys

from bs4 import BeautifulSoup
import soupsieve as sv

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSS = os.path.join(ROOT, "Card 1 - Style.css")
FIXTURES = os.path.join(HERE, "fixtures")

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}")
    if cond:
        PASS += 1
    else:
        FAIL += 1


def load_hide_selectors():
    """Pull every display:none rule from the 6b compactor section."""
    with open(CSS, encoding="utf-8") as f:
        css = f.read()
    # Anchor on the first rule's comment, not the section banner (the banner
    # comment wraps the "6b." marker itself and would leak header text).
    start = css.index("/* --- Collapse all dictionary entries after the first --- */")
    end = css.index("7. CIRCULAR AUDIO BUTTON")
    block = css[start:end]
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    selectors = []
    for rule in re.findall(r"([^{}]+)\{[^{}]*display:\s*none[^{}]*\}", block):
        sel = " ".join(rule.split())
        if sel and not sel.startswith("@"):
            for part in sel.split(","):
                part = part.strip()
                if part:
                    selectors.append(part)
    if not selectors:
        raise RuntimeError("no compactor display:none rules found in CSS")
    return selectors


def visible_text(html):
    """Text after applying all hide rules (hidden subtrees removed)."""
    soup = BeautifulSoup(html, "html.parser")
    for sel in load_hide_selectors():
        for el in sv.select(sel, soup):
            el.decompose()
    return " ".join(soup.get_text().split())


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read().strip()


def apply_prune(html):
    """Mirror of Back's pruneCompactedGlossary: remove exactly what the §6b
    hide rules hide. Grouped per parent like CSS `~`.

    Chinese port: the Japanese structured-content selectors (語義G,
    data-sc-l3*, 補説G, 可能形, …) are gone because Chinese Yomitan
    dictionaries emit no such markup. Keep this list identical to the
    dropFrom/remove calls in the back script or the mirror check below
    stops being meaningful."""
    soup = BeautifulSoup(html, "html.parser")
    for box in sv.select(".primary-definition", soup):
        for sel, keep in [
            (".yomitan-glossary > ol > li", 1),
            (".yomitan-glossary > ul > li", 1),
            ('[data-sc-content="glossary"] > li', 2),
            ('[data-sc-content="glossary"] > ul > li', 2),
        ]:
            groups = {}
            for el in sv.select(sel, box):
                groups.setdefault(id(el.parent), []).append(el)
            for group in groups.values():
                for el in group[keep:]:
                    el.decompose()
        for el in box.select(
            '[data-sc-content="forms"], div[data-sc-content="attribution"], '
            'span[data-sc-content="attribution"], i'
        ):
            el.decompose()
    return soup


def main():
    # --- 1. Plain-gloss Chinese dictionary (CC-CEDICT-style) ---
    field = f'<div class="definition-box primary-definition">{fixture("yomitan_chinese_gloss.html")}</div>'
    out = visible_text(field)
    check("plain: headword kept", "学习" in out)
    check("plain: gloss 1 kept", "to study; to learn" in out)
    check("plain: gloss 2 kept", "learning; study" in out)
    check("plain: gloss 3+ hidden", "THIS THIRD SENSE MUST BE HIDDEN" not in out
          and "another sense that must be hidden" not in out)
    check("plain: second dictionary hidden",
          "SECOND DICTIONARY MUST BE HIDDEN ENTIRELY" not in out)

    # --- 1b. Structured Chinese dictionary (labels, forms, attribution,
    #        sub-entry, and a <ul> glossary instead of <ol>) ---
    field = f'<div class="definition-box primary-definition">{fixture("yomitan_chinese_structured.html")}</div>'
    out = visible_text(field)
    check("struct: headword kept", "学习" in out)
    check("struct: sense 1 kept", "to study; to learn" in out)
    check("struct: sense 2 kept", "learning; study" in out)
    check("struct: sense 3+ hidden", "THIRD SENSE MUST BE HIDDEN" not in out)
    check("struct: dictionary label <i> hidden", "(Chinese Wiktionary)" not in out)
    check("struct: sub-entry word 学习者 hidden", "学习者" not in out)
    check("struct: forms appendix hidden", "present" not in out)
    check("struct: attribution hidden", "CC BY-SA" not in out)

    # --- 2c. Extended-definition FALLBACK box (when Definition is absent)
    #     must be compacted identically (it also carries primary-definition) ---
    field = f'<div class="definition-box primary-definition">{fixture("yomitan_chinese_structured.html")}</div>'
    out_fallback = visible_text(field)
    check("fallback: compacted like main Definition",
          "(Chinese Wiktionary)" not in out_fallback and "学习者" not in out_fallback
          and "to study; to learn" in out_fallback)

    # --- 3. Extended definition control (must be UNTOUCHED) ---
    ext = fixture("extended_definition_control.html")
    out = visible_text(ext)
    check("ext: third sense still visible", "THIS THIRD SENSE MUST REMAIN VISIBLE." in out)
    check("ext: second dictionary still visible", "SECOND DICTIONARY MUST REMAIN VISIBLE." in out)

    # --- 4. Scope guard: selectors must all be prefixed .primary-definition ---
    leaked = [s for s in load_hide_selectors() if not s.startswith(".primary-definition")]
    check("all hide rules scoped to .primary-definition", not leaked)

    # --- 5. Prune mirror (BLOAT-01A): JS removal == CSS hiding, per fixture ---
    for name in ("yomitan_chinese_gloss.html", "yomitan_chinese_structured.html"):
        field = f'<div class="definition-box primary-definition">{fixture(name)}</div>'
        css_only = visible_text(field)
        pruned = apply_prune(field)
        leftover = [s for s in load_hide_selectors() if sv.select(s, pruned)]
        check(f"prune removes everything CSS would hide ({name})", not leftover)
        check(f"prune preserves visible text ({name})",
              visible_text(str(pruned)) == css_only)

    print()
    print(f"{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
