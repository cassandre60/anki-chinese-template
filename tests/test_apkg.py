#!/usr/bin/env python3
"""Release-asset verification tests.

The apkg is the one artifact other people install, and `exportPackage`
returns `True` whether or not it put anything useful in the file. These
tests build packages in-memory the way Anki does and check that
`export_apkg.verify()`:

  - ACCEPTS a correct package (Chinese note type, Chinese deck, 3 notes);
  - REJECTS a package with no note type — the real failure mode, an empty
    deck exported as a package that installs nothing;
  - REJECTS a package carrying a different note type;
  - REJECTS a note-count mismatch;
  - READS `collection.anki21`, not `collection.anki2`.

The last one is a regression test for a bug this repository actually
shipped once: an apkg contains TWO databases, and `collection.anki2`
holds a fixed set of stock note types (Basic, Cloze, Image Occlusion)
plus one Default-deck card. A verifier that reads it "sees" Basic note
types for a perfectly good Chinese package. See docs/adr/009.

Run directly:  python3 tests/test_apkg.py
Wired into ./verify.

Dependencies: stdlib only (no Anki needed).
"""
import io
import contextlib
import json
import os
import sqlite3
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import export_apkg  # noqa: E402

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


# --- fixture builders -------------------------------------------------------

CHINESE_MODEL = {
    "id": 1, "name": export_apkg.MODEL_NAME, "type": 0, "mod": 0, "usn": -1,
    "sortf": 0, "did": 1,
    "tmpls": [{"name": "Card 1", "ord": 0, "qfmt": "{{Expression}}",
               "afmt": "{{Expression}}", "did": None, "bqfmt": "",
               "bafmt": "", "bfont": "", "bsize": 0}],
    "flds": [{"name": "Expression", "ord": 0, "sticky": False, "rtl": False,
              "font": "Arial", "size": 20, "description": "",
              "plainText": False, "collapsed": False,
              "excludeFromSearch": False}],
    "css": "/* css */", "latexPre": "", "latexPost": "",
}

BASIC_MODEL = dict(CHINESE_MODEL, id=2, name="Basic")

STOCK_MODELS = {
    "10": {"id": 10, "name": "Basic"},
    "11": {"id": 11, "name": "Cloze"},
    "12": {"id": 12, "name": "Image Occlusion"},
}


def build_package(path, models, decks, notes, vestigial=True):
    """Write an apkg shaped exactly like Anki's: the real content in
    collection.anki21, and — when `vestigial` — a second database holding
    stock note types, which is what Anki really does."""
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, export_apkg.LEGACY_DB)
    con = sqlite3.connect(db)
    con.execute("""CREATE TABLE col (id integer primary key, crt integer not null,
        mod integer not null, scm integer not null, ver integer not null,
        dty integer not null, usn integer not null, ls integer not null,
        conf text not null, models text not null, decks text not null,
        dconf text not null, tags text not null)""")
    con.execute("""CREATE TABLE notes (id integer primary key, guid text not null,
        mid integer not null, mod integer not null, usn integer not null,
        tags text not null, flds text not null, sfld integer not null,
        csum integer not null, flags integer not null, data text not null)""")
    con.execute("""CREATE TABLE cards (id integer primary key, nid integer not null,
        did integer not null, ord integer not null, mod integer not null,
        usn integer not null, type integer not null, queue integer not null,
        due integer not null, ivl integer not null, factor integer not null,
        reps integer not null, lapses integer not null, left integer not null,
        odue integer not null, odid integer not null, flags integer not null,
        data text not null)""")
    con.execute("INSERT INTO col VALUES (1,0,0,0,11,0,0,0,'{}',?,?,'{}','{}')",
                (json.dumps(models), json.dumps(decks)))
    con.executemany("INSERT INTO notes VALUES (?,?,?,0,-1,'',?,?,0,0,'')",
                    [(i + 1, f"g{i}", 1, n, n) for i, n in enumerate(notes)])
    con.executemany("INSERT INTO cards VALUES (?,?,?,0,0,-1,0,0,0,0,0,0,0,0,0,0,0,'')",
                    [(i + 1, i + 1, 1) for i in range(len(notes))])
    con.commit()
    con.close()

    meta = os.path.join(tmpdir, "meta")
    with open(meta, "w", encoding="utf-8") as f:
        json.dump({"key": "anki-chinese-template", "value": 11}, f)

    # The vestigial companion is a real sqlite file holding stock note
    # types — this is what Anki actually writes alongside the legacy db.
    vest = None
    if vestigial:
        vest = os.path.join(tmpdir, "vest.anki2")
        con = sqlite3.connect(vest)
        con.execute("""CREATE TABLE col (id integer primary key, crt integer not null,
            mod integer not null, scm integer not null, ver integer not null,
            dty integer not null, usn integer not null, ls integer not null,
            conf text not null, models text not null, decks text not null,
            dconf text not null, tags text not null)""")
        con.execute("INSERT INTO col VALUES (1,0,0,0,11,0,0,0,'{}',?,?,'{}','{}')",
                    (json.dumps(STOCK_MODELS),
                     json.dumps({"1": {"id": 1, "name": "Default"}})))
        con.commit()
        con.close()

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(meta, "meta")
        z.write(db, export_apkg.LEGACY_DB)
        if vest:
            z.write(vest, "collection.anki2")
        z.writestr("media", "{}")


DECKS = {
    "1": {"id": 1, "name": "Default"},
    "2": {"id": 2, "name": "My Life Decks"},
    "3": {"id": 3, "name": "My Life Decks::Chinese"},
}


def run_verify(path, expected):
    """Point export_apkg at `path` and capture its verdict + message."""
    original = export_apkg.EXPORT_PATH
    export_apkg.EXPORT_PATH = path
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink):
            ok = export_apkg.verify(expected)
    finally:
        export_apkg.EXPORT_PATH = original
    return ok, sink.getvalue()


def main():
    tmp = tempfile.mkdtemp()

    # --- 1. A correct package is accepted ---------------------------------
    good = os.path.join(tmp, "good.apkg")
    build_package(good, {"1": CHINESE_MODEL}, DECKS, ["学习", "窗户", "图书馆"])
    ok, msg = run_verify(good, 3)
    check("accepts a correct package", ok is True, msg)

    # --- 2. REGRESSION: the vestigial collection.anki2 must not be read ---
    # This package is identical to `good` except that it also contains the
    # stock-note-type database Anki always writes. A verifier reading
    # collection.anki2 sees only Basic/Cloze/Image Occlusion and rejects.
    models, decks, notes = export_apkg.inspect(good)
    check("reads collection.anki21, not collection.anki2",
          export_apkg.MODEL_NAME in models,
          f"got {models}")
    with zipfile.ZipFile(good) as z:
        entries = set(z.namelist())
    check("the fixture really does contain both databases",
          {"collection.anki21", "collection.anki2"} <= entries, str(entries))
    with zipfile.ZipFile(good) as z:
        with tempfile.TemporaryDirectory() as td:
            z.extract("collection.anki2", td)
            con = sqlite3.connect(os.path.join(td, "collection.anki2"))
            vest_models = json.loads(con.execute("select models from col").fetchone()[0])
            con.close()
    check("reading collection.anki2 would have missed our note type",
          export_apkg.MODEL_NAME not in vest_models
          and {m["name"] for m in vest_models.values()} == {"Basic", "Cloze", "Image Occlusion"},
          str([m["name"] for m in vest_models.values()]))

    # --- 3. The real failure mode: empty deck exported as an empty package --
    empty = os.path.join(tmp, "empty.apkg")
    build_package(empty, {}, DECKS, [])
    ok, msg = run_verify(empty, 3)
    check("REJECTS a package with no note type (empty deck export)", ok is False)
    check("  and names the missing note type",
          export_apkg.MODEL_NAME in msg, msg)

    # --- 4. Wrong note type ------------------------------------------------
    wrong = os.path.join(tmp, "wrong.apkg")
    build_package(wrong, {"1": BASIC_MODEL}, DECKS, ["a", "b", "c"])
    ok, msg = run_verify(wrong, 3)
    check("REJECTS a package carrying a different note type", ok is False)
    check("  and says which type it expected", export_apkg.MODEL_NAME in msg, msg)

    # --- 5. Wrong note count ----------------------------------------------
    ok, msg = run_verify(good, 7)
    check("REJECTS a note-count mismatch", ok is False)
    check("  and prints both numbers", "3" in msg and "7" in msg, msg)

    # --- 6. Missing deck ---------------------------------------------------
    nodeck = os.path.join(tmp, "nodeck.apkg")
    build_package(nodeck, {"1": CHINESE_MODEL}, {"1": {"id": 1, "name": "Default"}},
                  ["a", "b", "c"])
    ok, msg = run_verify(nodeck, 3)
    check("REJECTS a package without the Chinese deck", ok is False)
    check("  and says so", "Chinese" in msg, msg)

    # --- 7. Structurally broken file --------------------------------------
    junk = os.path.join(tmp, "junk.apkg")
    with zipfile.ZipFile(junk, "w") as z:
        z.writestr("meta", "{}")
    ok, msg = run_verify(junk, 3)
    check("REJECTS a package missing collection.anki21", ok is False)

    print()
    print(f"{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
