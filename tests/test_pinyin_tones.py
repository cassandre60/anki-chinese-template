#!/usr/bin/env python3
"""Pinyin tone-coloring tests.

Extracts applyPinyinTones verbatim from the real
`Card 1 - Back.template.anki` and runs it in headless Chrome against
plain-text Pinyin fields, asserting the produced tone-N classes:

  - diacritic style ("zhōng guó")     → tone 1 / tone 2
  - numeric style  ("zhong1 guo2")     → tone 1 / tone 2
  - neutral syllable ("de", "le")      → tone 0
  - ü variants (lǜ / nǚ)               → tone 3 / tone 3
  - 5th (neutral) tone written as 5    → tone 5
  - markup inside the field is left alone (never rewritten)
  - idempotent: a second pass is a no-op
  - hidden line keeps its classes after a P toggle

Run directly:  python3 tests/test_pinyin_tones.py
Wired into ./verify. Skipped gracefully without Chrome.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BACK = os.path.join(ROOT, "Card 1 - Back.template.anki")
CHROME = (shutil.which("google-chrome") or shutil.which("google-chrome-stable")
          or shutil.which("chromium") or shutil.which("chromium-browser"))

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    tag = "PASS" if cond else "FAIL"
    print(f"[{tag}] {name}" + (f" ({detail})" if detail and not cond else ""))
    if cond:
        PASS += 1
    else:
        FAIL += 1


def load_function():
    with open(BACK, encoding="utf-8") as f:
        back = f.read()
    # The tone table is a const declared just above the function; both are
    # needed verbatim or the function throws on first lookup.
    const = re.search(r"const PINYIN_TONE_MARKS = \{.*?\};", back, re.S)
    fn = re.search(r"window\.applyPinyinTones = function.*?^\s{4}\};", back, re.S | re.M)
    if not const or not fn:
        raise RuntimeError("applyPinyinTones / PINYIN_TONE_MARKS not found in back template")
    return const.group(0) + "\n" + fn.group(0)


def render(fn_src, pinyin_html, wrap_class="pinyin-display"):
    html = f"""<!doctype html><html><head><meta charset="utf-8"></head><body>
<div class="card-wrapper back-card">
  <div class="{wrap_class}">{pinyin_html}</div>
  <div class="hero-word-wrap"><div class="word-display">测试</div></div>
</div>
<script>
var report = {{}};
try {{
{fn_src}
var el = document.querySelector('.{wrap_class}');
window.applyPinyinTones();
report.classes = Array.prototype.map.call(el.querySelectorAll('span'), function(s) {{
  return s.className + ':' + s.textContent;
}});
report.text = el.textContent;
report.applied = el.dataset.tonesApplied === '1';
/* idempotence: a second pass must not re-wrap */
window.applyPinyinTones();
report.classesAfterSecond = Array.prototype.map.call(el.querySelectorAll('span'), function(s) {{
  return s.className + ':' + s.textContent;
}});
/* P toggle: classes survive, only visibility changes */
var w = document.querySelector('.card-wrapper');
w.classList.add('pinyin-hidden');
report.hiddenStillHasSpans = el.querySelectorAll('span').length;
w.classList.remove('pinyin-hidden');
}} catch(e) {{ report.err = String(e && e.stack || e); }}
document.title = 'X' + JSON.stringify(report) + 'X';
</scr""" + "ipt></body></html>"
    import json as _json
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "pinyin.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            out = subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                 "--hide-scrollbars", "--window-size=800,600",
                 "--virtual-time-budget=1500", "--dump-dom", f"file://{path}"],
                capture_output=True, text=True, timeout=60,
            ).stdout
        except subprocess.TimeoutExpired:
            return None
    m = re.search(r"<title>X(.*?)X</title>", out, re.S)
    if not m:
        return None
    try:
        return _json.loads(m.group(1))
    except ValueError:
        return None


def main():
    if not CHROME:
        print("[SKIP] no headless Chrome found — Pinyin tone checks skipped")
        return 0
    fn = load_function()

    # --- 1. Diacritic style, multi-syllable ---
    r = render(fn, "zhōng guó")
    check("diacritics: probe returned", r is not None)
    if r:
        check("diacritics: no error", "err" not in r, r.get("err", ""))
        check("diacritics: tone 1 then tone 2",
              r.get("classes") == ["tone-1:zhōng", "tone-2:guó"], str(r.get("classes")))
        check("diacritics: spacing preserved", r.get("text") == "zhōng guó", repr(r.get("text")))
        check("diacritics: marked applied", r.get("applied") is True)
        check("diacritics: second pass is a no-op",
              r.get("classesAfterSecond") == r.get("classes"), str(r.get("classesAfterSecond")))
        check("diacritics: P toggle keeps the tone spans",
              r.get("hiddenStillHasSpans") == 2, str(r.get("hiddenStillHasSpans")))

    # --- 2. ü variants: ǖǘǚǜ carry the same four tones as a/o/e ---
    r = render(fn, "lǜ jiā")
    if r:
        check("ü: lǜ is tone 4, jiā is tone 1",
              r.get("classes") == ["tone-4:lǜ", "tone-1:jiā"], str(r.get("classes")))
    r = render(fn, "lǚ nǚ")
    if r:
        check("ü: lǚ/nǚ are tone 3",
              r.get("classes") == ["tone-3:lǚ", "tone-3:nǚ"], str(r.get("classes")))

    # --- 3. Neutral syllables (no diacritic) ---
    r = render(fn, "de le ma")
    if r:
        check("neutral: all tone 0",
              r.get("classes") == ["tone-0:de", "tone-0:le", "tone-0:ma"], str(r.get("classes")))

    # --- 4. Numeric style ---
    r = render(fn, "zhong1 guo2")
    if r:
        check("numeric: tone 1 then tone 2",
              r.get("classes") == ["tone-1:zhong1", "tone-2:guo2"], str(r.get("classes")))
    r = render(fn, "ma5")
    if r:
        check("numeric: 5 folds onto neutral tone-0",
              r.get("classes") == ["tone-0:ma5"], str(r.get("classes")))
    r = render(fn, "zhong0 guo4")
    if r:
        check("numeric: 0 is neutral",
              r.get("classes") == ["tone-0:zhong0", "tone-4:guo4"], str(r.get("classes")))

    # --- 5. Markup inside the field is never rewritten (mined fields may
    #        carry <b>/numbers; the controller must not destroy them) ---
    r = render(fn, "zhōng <b>guó</b>")
    if r:
        check("markup: field left untouched", r.get("classes") == [], str(r.get("classes")))
        check("markup: text preserved verbatim", r.get("text") == "zhōng guó", repr(r.get("text")))

    # --- 6. Sentence Pinyin uses the same controller ---
    r = render(fn, "tīng yīn yuè", wrap_class="sentence-pinyin")
    if r:
        check("sentence pinyin: tone 1, 1, 4",
              r.get("classes") == ["tone-1:tīng", "tone-1:yīn", "tone-4:yuè"],
              str(r.get("classes")))

    # --- 7. {{edit:}} wrapper (single EFDRC div): tone the text inside it ---
    r = render(fn, '<div data-EFDRCfield="UGlueWlu" class="EFDRC-outline EFDRC-ctrl ">zhōng guó</div>')
    if r:
        check("edit wrapper: tone 1 then tone 2",
              r.get("classes") == ["tone-1:zhōng", "tone-2:guó"], str(r.get("classes")))
        check("edit wrapper: spacing preserved",
              r.get("text") == "zhōng guó", repr(r.get("text")))
        check("edit wrapper: marked applied", r.get("applied") is True)
        check("edit wrapper: second pass is a no-op",
              r.get("classesAfterSecond") == r.get("classes"), str(r.get("classesAfterSecond")))
    r = render(fn, '<div data-EFDRCfield="U2VudGVuY2UgUGlueWlu" class="EFDRC-outline EFDRC-ctrl ">tīng yīn yuè</div>',
               wrap_class="sentence-pinyin")
    if r:
        check("edit wrapper sentence: tone 1, 1, 4",
              r.get("classes") == ["tone-1:tīng", "tone-1:yīn", "tone-4:yuè"],
              str(r.get("classes")))

    # --- 8. No over-descend: already-toned or non-EFDRC markup stays put ---
    r = render(fn, '<div data-EFDRCfield="eXhk"><span class="tone-1">zhōng</span></div>')
    if r:
        check("edit wrapper already toned: left alone",
              r.get("classes") == ["tone-1:zhōng"], str(r.get("classes")))
        check("edit wrapper already toned: not re-marked", r.get("applied") is not True)
    r = render(fn, '<div class="other">zhōng guó</div>')
    if r:
        check("non-EFDRC wrapper: left untouched", r.get("classes") == [], str(r.get("classes")))

    # --- 9. Bracket readings (字[pinyin]) stack furigana-style ---
    r = render(fn, "对[duì] 投[tóu] 资[zī]")
    if r:
        check("brackets: tone 4, 2, 1 with stacked pysub readings, no brackets shown",
              r.get("classes") == ["tone-4 pystack:对duì", "pysub:duì",
                                   "tone-2 pystack:投tóu", "pysub:tóu",
                                   "tone-1 pystack:资zī", "pysub:zī"],
              str(r.get("classes")))
        check("brackets: storage text intact (display drops brackets)",
              r.get("text") == "对duì 投tóu 资zī", repr(r.get("text")))
        check("brackets: second pass is a no-op",
              r.get("classesAfterSecond") == r.get("classes"), str(r.get("classesAfterSecond")))

    print()
    print(f"{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
