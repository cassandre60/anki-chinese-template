#!/usr/bin/env python3
"""Export the Chinese sample deck to dist/anki-chinese-template.apkg, then VERIFY it.

Called by finish.sh; can also be run standalone.

STEP 1 — export, over Anki-Connect `exportPackage`
    The one export action Anki-Connect exposes, and it works: the deck
    limiter is honoured, so the package carries the Chinese note type and
    only this deck's cards.

STEP 2 — verify what was actually written
    `exportPackage` returns `True` on success and Anki writes a
    structurally valid apkg in every case we have seen, including the case
    that matters most: **a deck with no cards produces a package with no
    note type at all** (verified — an empty deck exports `models: []`, not
    a fallback to the Default deck). That package imports "successfully"
    and leaves the user with nothing. So success is not evidence; the file
    is re-opened and checked before the release is allowed to continue.

WHY THE VERIFICATION READS `collection.anki21` AND NOT `collection.anki2`
    An apkg contains two databases:
      collection.anki21 — the legacy schema that actually holds the data
      collection.anki2  — a vestigial companion holding a fixed set of
                           stock note types (Basic, Cloze, Image
                           Occlusion…) that is NOT the exported content
    A verification pass that reads `collection.anki2` will "see" Basic
    note types and one card in the Default deck for a package that in fact
    contains the Chinese note type and 3 Chinese cards. It will conclude
    the export is broken when it is fine, or — far worse — conclude it is
    fine for the wrong reasons. (This repo shipped exactly that mistake
    once; see docs/adr/009.) `collection.anki21` is the only file to trust.

Requires: Anki running with Anki-Connect.
Standard library only.
"""
import json
import os
import sqlite3
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"
DECK_NAME = "My Life Decks::Chinese"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_PATH = os.path.join(SCRIPT_DIR, "dist", "anki-chinese-template.apkg")
LEGACY_DB = "collection.anki21"


def _anki(action, **params):
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
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


def export():
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
    live_cards = _anki("findCards", query=f'"deck:{DECK_NAME}"')
    if not live_cards:
        # Anki happily exports a deck with zero cards as a package with no
        # note type in it. Say so up front instead of shipping that.
        print(f"ERROR: deck '{DECK_NAME}' has no cards.")
        print("       Anki exports an empty deck as a package containing NO note type,")
        print("       which imports cleanly and installs nothing.")
        print("       Seed it first:  python3 seed_sample_cards.py")
        sys.exit(1)
    ok = _anki("exportPackage", deck=DECK_NAME, path=EXPORT_PATH, includeSched=False)
    if not ok or not os.path.isfile(EXPORT_PATH) or os.path.getsize(EXPORT_PATH) == 0:
        print("ERROR: exportPackage did not produce a usable file")
        sys.exit(1)
    return len(live_cards)


def inspect(path):
    """Return (model_names, deck_names, note_count) from the LEGACY database."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        missing = [e for e in ("meta", LEGACY_DB, "media") if e not in names]
        if missing:
            raise ValueError(f"apkg is missing {missing}")
        with tempfile.TemporaryDirectory() as td:
            z.extract(LEGACY_DB, td)
            con = sqlite3.connect(os.path.join(td, LEGACY_DB))
            try:
                models = json.loads(con.execute("select models from col").fetchone()[0])
                decks = json.loads(con.execute("select decks from col").fetchone()[0])
                notes = con.execute("select count(*) from notes").fetchone()[0]
            finally:
                con.close()
    return ([m.get("name") for m in models.values()],
            [d.get("name") for d in decks.values()],
            notes)


def verify(expected_notes):
    problems = []
    try:
        model_names, deck_names, note_count = inspect(EXPORT_PATH)
    except Exception as e:
        print(f"ERROR: could not read the exported package: {e}")
        return False

    if MODEL_NAME not in model_names:
        problems.append(
            f"the package does not contain '{MODEL_NAME}' (it has: {model_names})")
    if not any(name and name.endswith("Chinese") for name in deck_names):
        problems.append(f"the package does not contain the 'Chinese' deck (it has: {deck_names})")
    if note_count != expected_notes:
        problems.append(
            f"the package has {note_count} notes, but the deck has {expected_notes} cards")

    if problems:
        print("ERROR: the exported apkg is not what the release promises:")
        for p in problems:
            print(f"  - {p}")
        print("       Refusing to publish. The file is kept at "
              f"{os.path.relpath(EXPORT_PATH, SCRIPT_DIR)} for inspection.")
        return False
    return True


def main() -> int:
    expected = export()
    if not verify(expected):
        return 1
    print(f"Export OK: {EXPORT_PATH} "
          f"({os.path.getsize(EXPORT_PATH) / 1e6:.2f} MB, {expected} card(s), "
          f"verified: '{MODEL_NAME}' present in {LEGACY_DB})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
