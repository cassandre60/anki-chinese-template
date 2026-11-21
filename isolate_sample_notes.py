#!/usr/bin/env python3
"""One-shot: move the sample-tagged notes into the dedicated sample deck.

Run once, by hand, from the repo root:

    python3 isolate_sample_notes.py

WHY THIS EXISTS
---------------
The release exports a dedicated sample deck
(`My Life Decks::Chinese::anki-chinese-template`), but the samples were
originally seeded into the study deck `My Life Decks::Chinese` before that
deck existed. This script creates the sample deck (idempotent) and moves
every card whose note carries the `anki-chinese-template-sample` tag into
it, so `export_apkg.py --release` no longer sees real study cards.

It never touches untagged notes (mined cards stay where they are), and
re-running it is a no-op.

Requires: Anki running with Anki-Connect.
"""
import json
import sys
import urllib.request

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
SAMPLE_DECK_NAME = "My Life Decks::Chinese::anki-chinese-template"
SAMPLE_TAG = "anki-chinese-template-sample"


def _anki(action, **params):
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: cannot reach Anki-Connect at {ANKI_CONNECT_URL} ({e}). "
              "Is Anki running with the add-on?")
        sys.exit(1)
    if result.get("error"):
        print(f"ERROR: Anki-Connect returned: {result['error']}")
        sys.exit(1)
    return result.get("result")


def main():
    decks = _anki("deckNames")
    if SAMPLE_DECK_NAME in decks:
        print(f"sample deck ready: {SAMPLE_DECK_NAME}")
    else:
        _anki("createDeck", deck=SAMPLE_DECK_NAME)
        print(f"created sample deck: {SAMPLE_DECK_NAME}")

    cards = _anki("findCards", query=f'"tag:{SAMPLE_TAG}"')
    if not cards:
        print(f"no cards tagged '{SAMPLE_TAG}' — nothing to move")
        return 0
    _anki("changeDeck", cards=cards, deck=SAMPLE_DECK_NAME)
    in_sample = _anki("findCards", query=f'"deck:{SAMPLE_DECK_NAME}"')
    print(f"moved {len(cards)} tagged card(s) into the sample deck "
          f"({len(in_sample)} card(s) now in it)")
    print()
    print("Next: python3 export_apkg.py --release   # should now pass the gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
