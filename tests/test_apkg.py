#!/usr/bin/env python3
"""apkg builder tests.

`build_apkg.py` is a hard gate in the release loop: a release asset that
installs the wrong note type is worse than no asset. These tests exercise
the pure parts of it (collection assembly, zip writing, verification)
without needing Anki, so CI covers the same code the release runs.

Run directly:  python3 tests/test_apkg.py
Wired into ./verify.

Dependencies: stdlib only.
"""
import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import build_apkg  # noqa: E402

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


FIELD_NAMES = ["Expression", "Definition", "Sentence", "Pinyin", "Frequency"]


def fake_model():
    return {
        "id": build_apkg.MODEL_ID,
        "name": build_apkg.MODEL_NAME,
        "type": 0, "mod": 0, "usn": -1, "sortf": 0, "did": build_apkg.DECK_ID,
        "tmpls": [{
            "name": "Card 1", "ord": 0,
            "qfmt": "<div>{{Expression}}</div>", "afmt": "<div>{{Expression}}</div>",
            "did": None, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0,
        }],
        "flds": [
            {"name": n, "ord": i, "sticky": False, "rtl": False, "font": "Arial",
             "size": 20, "description": "", "plainText": False, "collapsed": False,
             "excludeFromSearch": False}
            for i, n in enumerate(FIELD_NAMES)
        ],
        "css": "/* css */",
        "latexPre": "", "latexPost": "",
        "req": [[0, "any", [0]]],
        "tags": [],
    }


def fake_infos():
    return [
        {"noteId": 100, "tags": ["anki-chinese-template-sample"],
         "fields": {"Expression": {"value": "学习"}, "Definition": {"value": "<b>to learn</b>"},
                    "Sentence": {"value": "他每天学习。"}, "Pinyin": {"value": "xué xí"},
                    "Frequency": {"value": "1200"}}},
        {"noteId": 101, "tags": ["anki-chinese-template-sample", "listening"],
         "fields": {"Expression": {"value": "图书馆"}, "Definition": {"value": ""},
                    "Sentence": {"value": "图书馆关门。"}, "Pinyin": {"value": "tú shū guǎn"},
                    "Frequency": {"value": ""}}},
    ]


def build(path, model=None, infos=None):
    model = model or fake_model()
    infos = fake_infos() if infos is None else infos
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "collection.anki21")
        count = build_apkg.build_collection(model, infos, FIELD_NAMES, db)
        build_apkg.write_apkg(db, path)
    return count


def read_col(path):
    import zipfile
    with zipfile.ZipFile(path) as z:
        td = tempfile.mkdtemp()
        z.extract("collection.anki21", td)
        con = sqlite3.connect(os.path.join(td, "collection.anki21"))
        col = json.loads(con.execute("select models from col").fetchone()[0])
        decks = json.loads(con.execute("select decks from col").fetchone()[0])
        tags = json.loads(con.execute("select tags from col").fetchone()[0])
        notes = con.execute("select flds, tags, sfld from notes order by id").fetchall()
        cards = con.execute("select nid, did, ord, type, queue from cards order by id").fetchall()
        ver = con.execute("select ver from col").fetchone()[0]
        con.close()
    return col, decks, tags, notes, cards, ver


def main():
    path = os.path.join(tempfile.mkdtemp(), "test.apkg")
    count = build(path)

    check("build: note count reported", count == 2, str(count))
    check("build: verify_apkg accepts its own output",
          build_apkg.verify_apkg(path, 2) is True)

    col, decks, tags, notes, cards, ver = read_col(path)
    model = list(col.values())[0]
    check("apkg: schema version 11 (legacy, importable)", ver == 11, str(ver))
    check("apkg: carries our note type", model["name"] == build_apkg.MODEL_NAME,
          model["name"])
    check("apkg: carries the Chinese deck",
          [d.get("name") for d in decks.values()] == ["Chinese"],
          str([d.get("name") for d in decks.values()]))
    check("apkg: both notes present", len(notes) == 2, str(len(notes)))
    check("apkg: one card per note", len(cards) == 2, str(len(cards)))
    check("apkg: cards target the exported deck",
          all(c[1] == build_apkg.DECK_ID for c in cards), str(cards))
    check("apkg: cards are 'new' in queue 0",
          all(c[3] == 0 and c[4] == 0 for c in cards), str(cards))
    check("apkg: field values join with the 0x1f separator",
          notes[0][0].split("\x1f") == ["学习", "to learn", "他每天学习。", "xué xí", "1200"],
          notes[0][0])
    check("apkg: HTML is stripped from field text (Anki stores plain text)",
          "<b>" not in notes[0][0] and "to learn" in notes[0][0], notes[0][0])
    check("apkg: empty fields are preserved as empty segments",
          notes[1][0].split("\x1f")[1] == "", repr(notes[1][0]))
    check("apkg: sort field is the first field", notes[0][2] == "学习", notes[0][2])
    check("apkg: tags recorded on the note", "listening" in notes[1][1], notes[1][1])
    check("apkg: tags table lists every used tag",
          {"listening", "anki-chinese-template-sample"} <= set(tags), str(list(tags)))
    check("apkg: card ids unique", len({c[0] for c in cards}) == len(cards))

    # --- The gate must be able to FAIL. A verifier that always returns
    # True is worse than no verifier, because it converts a silent
    # wrong-asset bug into a green release.
    wrong = os.path.join(os.path.dirname(path), "wrong.apkg")
    build(wrong, model=dict(fake_model(), name="Basic (and reversed card)"))
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        rejected = build_apkg.verify_apkg(wrong, 2)
    check("verify: rejects a package carrying a different note type",
          rejected is False)
    check("verify: says WHY it rejected (names the expected model)",
          build_apkg.MODEL_NAME in sink.getvalue(), sink.getvalue())

    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        rejected_count = build_apkg.verify_apkg(path, 7)
    check("verify: rejects a note-count mismatch", rejected_count is False)
    check("verify: reports the count mismatch numbers",
          "2" in sink.getvalue() and "7" in sink.getvalue(), sink.getvalue())

    print()
    print(f"{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
