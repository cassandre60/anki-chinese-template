#!/usr/bin/env python3
"""Build dist/anki-chinese-template.apkg from the live Chinese deck.

Called by finish.sh; can also be run standalone.

WHY THIS EXISTS (and why it does not just call Anki-Connect)
-------------------------------------------------------------
The obvious implementation is `exportPackage` over Anki-Connect. **On this
machine that silently produces the wrong file.** Anki 26.09.3 is running
an Anki-Connect build declaring `max_point_version: 45` (Anki 25.x); its
`exportPackage` sets `exporter.did` after the exporter is constructed, the
newer backend ignores it, and the call succeeds while exporting the
**Default** deck. The result is a valid-looking apkg containing Basic/Cloze
note types and none of ours — a release asset that installs the wrong
thing and says nothing about it.

So the package is assembled here instead: read the real notes out of Anki
over Anki-Connect (which works), and write the apkg with stdlib
`sqlite3` + `zipfile`. Fully deterministic, no dependency on the
exporter, and independently verifiable — `verify_apkg()` re-opens the
file it just wrote and asserts the model, the deck, and the note count.

An apkg (schema 11) is a zip of:
    meta                 legacy stub
    collection.anki21    the collection database
    media                "{}" for an empty media map

Requires: Anki running with Anki-Connect (for the reads).
"""
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"
DECK_NAME = "My Life Decks::Chinese"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_PATH = os.path.join(SCRIPT_DIR, "dist", "anki-chinese-template.apkg")

SCHEMA_VERSION = 11
# Stable ids: the apkg is re-importable more than once without the ids
# drifting between builds.
MODEL_ID = 1790774627863
DECK_ID = 1790774649927
DCONF_ID = 1

DEFAULT_DCONF = {
    "id": DCONF_ID, "mod": 0, "name": "Default", "usn": -1,
    "maxTaken": 60, "autoplay": True, "timer": 0, "replayq": True,
    "new": {
        "bury": True, "delays": [1, 10], "initialFactor": 2500,
        "ints": [1, 4, 7], "order": 1, "perDay": 20,
    },
    "rev": {
        "bury": True, "ease4": 1.3, "fuzz": 0.05, "ivlFct": 1.0,
        "maxIvl": 36500, "perDay": 200, "hardFactor": 1.2,
    },
    "lapse": {
        "delays": [10], "leechAction": 0, "leechFails": 8, "minInt": 1,
        "mult": 0,
    },
    "dyn": False, "newMix": 0, "newPerDayMinimum": 0, "interdayLearningMix": 0,
    "reviewOrder": 0, "newSortOrder": 0, "newGatherPriority": 0,
    "buryInterdayLearning": False,
}

DEFAULT_CONF = {
    "nextPos": 1, "sortType": "noteFld", "curDeck": DECK_ID, "newSpread": 0,
    "collapseTime": 1200,
}


def _anki(action, **params):
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError:
        print("ERROR: cannot reach Anki-Connect (is Anki running with the add-on?)")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: request failed: {e}")
        sys.exit(1)
    if result.get("error"):
        print(f"ERROR: Anki-Connect returned: {result['error']}")
        sys.exit(1)
    return result.get("result")


def _strip_html(value: str) -> str:
    """Anki stores note fields as plain text; a template with HTML in a
    field keeps it escaped, not raw. A mined glossary arrives as HTML, so
    it must be stored the way Anki would store it."""
    out = []
    in_tag = False
    for ch in value:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            out.append(ch)
    return "".join(out)


def read_live():
    """Pull the model, the deck's notes, and their cards out of Anki."""
    templates = _anki("modelTemplates", modelName=MODEL_NAME)
    if not templates:
        print(f"ERROR: no templates for model '{MODEL_NAME}'")
        sys.exit(1)
    model = {
        "id": MODEL_ID,
        "name": MODEL_NAME,
        "type": 0,
        "mod": int(time.time()),
        "usn": -1,
        "sortf": 0,
        "did": DECK_ID,
        "tmpls": [],
        "flds": [],
        "css": _anki("modelStyling", modelName=MODEL_NAME)["css"],
        "latexPre": (
            "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}"
            "\\usepackage{amssymb,amsmath,ul}\n\\pagestyle{empty}\n"
            "\\setlength{\\parindent}{0in}\n\\begin{document}\n"
        ),
        "latexPost": "\\end{document}",
    }

    # Field entries, in live order.
    names = _anki("modelFieldNames", modelName=MODEL_NAME)
    for i, name in enumerate(names):
        model["flds"].append({
            "name": name, "ord": i, "sticky": False, "rtl": False,
            "font": "Arial", "size": 20, "description": "",
            "plainText": False, "collapsed": False, "excludeFromSearch": False,
        })
    for name, pair in templates.items():
        model["tmpls"].append({
            "name": name, "ord": 0, "qfmt": pair["Front"], "afmt": pair["Back"],
            "did": None, "bqfmt": "", "bafmt": "", "bfont": "", "bsize": 0,
        })
    model["req"] = [[0, "any", [0]]]
    model["tags"] = []

    note_ids = _anki("findNotes", query=f'"deck:{DECK_NAME}"')
    if not note_ids:
        print(f"ERROR: deck '{DECK_NAME}' has no notes.")
        print("       Anki's exporter silently falls back to the Default deck when a")
        print("       deck is empty, so the apkg would carry the wrong note types.")
        print("       Seed it first:  python3 seed_sample_cards.py")
        sys.exit(1)
    infos = _anki("notesInfo", notes=note_ids)
    return model, infos, names


def build_collection(model, infos, field_names, path):
    now = int(time.time())
    col = {
        "crt": now, "mod": now, "scm": now, "ver": SCHEMA_VERSION,
        "dty": 0, "usn": 0, "ls": 0,
        "conf": DEFAULT_CONF,
        "models": {str(MODEL_ID): model},
        "decks": {str(DECK_ID): {
            "id": DECK_ID, "mod": now, "name": "Chinese", "usn": -1,
            "lrnToday": [0, 0], "revToday": [0, 0], "newToday": [0, 0],
            "timeToday": [0, 0], "collapsed": False, "browserCollapsed": False,
            "desc": "Chinese sentence-mining sample deck (delete the sample cards; "
                    "the note type is retained).",
            "dyn": 0, "conf": DCONF_ID, "extendNew": 0, "extendRev": 0,
            "reviewLimit": None, "newLimit": None,
            "reviewLimitToday": None, "newLimitToday": None,
        }},
        "dconf": {str(DCONF_ID): dict(DEFAULT_DCONF, mod=now)},
        "tags": {},
    }

    notes, cards = [], []
    all_tags = set()
    for i, info in enumerate(sorted(infos, key=lambda x: x["noteId"])):
        note_id = 1_700_000_000_000 + i
        values = [
            _strip_html((info.get("fields", {}).get(name, {}) or {}).get("value", ""))
            for name in field_names
        ]
        tags = " ".join(info.get("tags", []))
        all_tags.update(info.get("tags", []))
        sortf = values[0] if values else ""
        notes.append((
            note_id,
            hashlib.md5(str(note_id).encode()).hexdigest()[:10],
            MODEL_ID, now, -1, tags, "\x1f".join(values), sortf, 0, 0, "",
        ))
        cards.append((
            1_800_000_000_000 + i, note_id, DECK_ID, 0, now, -1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "",  # type..odid (0 = new)
        ))
    for tag in sorted(all_tags):
        col["tags"][tag] = None

    if os.path.exists(path):
        os.unlink(path)
    con = sqlite3.connect(path)
    try:
        con.execute("""CREATE TABLE col (
            id integer primary key, crt integer not null, mod integer not null,
            scm integer not null, ver integer not null, dty integer not null,
            usn integer not null, ls integer not null, conf text not null,
            models text not null, decks text not null, dconf text not null,
            tags text not null)""")
        con.execute("""CREATE TABLE notes (
            id integer primary key, guid text not null, mid integer not null,
            mod integer not null, usn integer not null, tags text not null,
            flds text not null, sfld integer not null, csum integer not null,
            flags integer not null, data text not null)""")
        con.execute("""CREATE TABLE cards (
            id integer primary key, nid integer not null, did integer not null,
            ord integer not null, mod integer not null, usn integer not null,
            type integer not null, queue integer not null, due integer not null,
            ivl integer not null, factor integer not null, reps integer not null,
            lapses integer not null, left integer not null, odue integer not null,
            odid integer not null, flags integer not null, data text not null)""")
        con.execute("""CREATE TABLE revlog (
            id integer primary key, cid integer not null, usn integer not null,
            ease integer not null, ivl integer not null, lastIvl integer not null,
            factor integer not null, time integer not null, type integer not null)""")
        con.execute("""CREATE TABLE graves (
            usn integer not null, oid integer not null, type integer not null)""")
        con.execute(
            "INSERT INTO col VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (1, col["crt"], col["mod"], col["scm"], col["ver"], col["dty"],
             col["usn"], col["ls"], json.dumps(col["conf"]),
             json.dumps(col["models"]), json.dumps(col["decks"]),
             json.dumps(col["dconf"]), json.dumps(col["tags"])),
        )
        con.executemany("INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)", notes)
        con.executemany("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", cards)
        con.commit()
    finally:
        con.close()
    return len(notes)


def write_apkg(collection_db, path):
    meta = json.dumps({"key": "anki-chinese-template", "value": SCHEMA_VERSION})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta", meta)
        z.write(collection_db, "collection.anki21")
        z.writestr("media", "{}")


def verify_apkg(path, expected_notes):
    """Re-open the file we just wrote and prove it carries OUR note type.

    A release asset that installs the wrong templates is worse than no
    asset, so this is a hard gate, not a courtesy check."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        for required in ("meta", "collection.anki21", "media"):
            if required not in names:
                print(f"ERROR: apkg is missing {required}")
                return False
        with tempfile.TemporaryDirectory() as td:
            z.extract("collection.anki21", td)
            con = sqlite3.connect(os.path.join(td, "collection.anki21"))
            models = json.loads(con.execute("select models from col").fetchone()[0])
            decks = json.loads(con.execute("select decks from col").fetchone()[0])
            note_count = con.execute("select count(*) from notes").fetchone()[0]
            con.close()
    model_names = [m["name"] for m in models.values()]
    deck_names = [d.get("name") for d in decks.values()]
    ok = True
    if MODEL_NAME not in model_names:
        print(f"ERROR: apkg does not contain '{MODEL_NAME}' (has: {model_names})")
        ok = False
    if "Chinese" not in deck_names:
        print(f"ERROR: apkg does not contain the 'Chinese' deck (has: {deck_names})")
        ok = False
    if note_count != expected_notes:
        print(f"ERROR: apkg has {note_count} notes, expected {expected_notes}")
        ok = False
    return ok


def main() -> int:
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    model, infos, field_names = read_live()
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "collection.anki21")
        count = build_collection(model, infos, field_names, db)
        write_apkg(db, EXPORT_PATH)
    if not verify_apkg(EXPORT_PATH, count):
        return 1
    print(f"Export OK: {EXPORT_PATH} "
          f"({os.path.getsize(EXPORT_PATH) / 1e6:.2f} MB, "
          f"{count} note(s), model '{MODEL_NAME}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
