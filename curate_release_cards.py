#!/usr/bin/env python3
"""One-shot: fill the release deck with a few of your own cards.

Run once, by hand, from the repo root:

    python3 curate_release_cards.py --count 5 --replace

WHY THIS EXISTS
---------------
The release exports the dedicated deck
`My Life Decks::Chinese::anki-chinese-template`. For a fresh profile the
synthetic notes from `seed_sample_cards.py` are enough, but the maintainer
wants the release to ship a few real mined cards instead. This script moves
the first N cards (by note id) from the study deck into the release deck
and tags them `anki-chinese-template-sample` so the release gate accepts
them.

Notes moved into a subdeck are still studied through the parent deck
`My Life Decks::Chinese` (Anki aggregates subdecks), so the study flow is
unchanged.

`--replace` first moves every card currently in the release deck back to
the study deck (use it to drop the synthetic samples). Without it the
script refuses when the release deck is non-empty.

Requires: Anki running with Anki-Connect.
"""
import argparse
import json
import sys
import urllib.request

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"
STUDY_DECK_NAME = "My Life Decks::Chinese"
RELEASE_DECK_NAME = "My Life Decks::Chinese::anki-chinese-template"
SAMPLE_TAG = "anki-chinese-template-sample"


def _anki(action, **params):
    req = urllib.request.Request(
        ANKI_CONNECT_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: cannot reach Anki-Connect at {ANKI_CONNECT_URL} ({e}). "
              "Is Anki running with the add-on?")
        sys.exit(1)
    if result.get("error"):
        print(f"ERROR: Anki-Connect returned: {result['error']}")
        sys.exit(1)
    return result.get("result")


def _card_ids(query):
    return _anki("findCards", query=query)


def _expressions(cards):
    """Map release-deck card ids to the Expression field, for the report."""
    notes = _anki("cardsToNotes", cards=cards)
    if not notes:
        return []
    return [i["fields"].get("Expression", {}).get("value", "") for i in
            _anki("notesInfo", notes=notes)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5,
                        help="how many real cards to put in the release deck")
    parser.add_argument("--replace", action="store_true",
                        help="move the release deck's current cards back to the study deck first")
    args = parser.parse_args()
    if args.count < 1:
        print("ERROR: --count must be >= 1")
        return 1

    decks = _anki("deckNames")
    if RELEASE_DECK_NAME not in decks:
        _anki("createDeck", deck=RELEASE_DECK_NAME)
        print(f"created release deck: {RELEASE_DECK_NAME}")

    existing = _card_ids(f'deck:"{RELEASE_DECK_NAME}"')
    if existing and not args.replace:
        print(f"REFUSING: the release deck already has {len(existing)} card(s).")
        print("Re-run with --replace to move them back to the study deck first.")
        return 1
    if existing:
        _anki("changeDeck", cards=existing, deck=STUDY_DECK_NAME)
        print(f"moved {len(existing)} card(s) from the release deck back to the study deck")

    # Study-deck cards, excluding the release subdeck and already-curated notes.
    query = (
        f'deck:"{STUDY_DECK_NAME}" '
        f'-deck:"{RELEASE_DECK_NAME}" '
        f'-tag:"{SAMPLE_TAG}"'
    )
    candidates = _card_ids(query)
    if not candidates:
        print("no study-deck candidates found — seed the release deck instead "
              "(python3 seed_sample_cards.py)")
        return 1
    notes = _anki("cardsToNotes", cards=candidates)
    ordered = sorted(zip(notes, candidates))  # by note id, deterministic
    chosen = ordered[: args.count]
    if len(chosen) < args.count:
        print(f"warning: only {len(chosen)} candidate(s) available")

    chosen_cards = [card for _, card in chosen]
    _anki("changeDeck", cards=chosen_cards, deck=RELEASE_DECK_NAME)
    _anki("addTags", notes=[note for note, _ in chosen], tags=SAMPLE_TAG)

    print(f"release deck now ships {len(chosen_cards)} card(s):")
    for expr in _expressions(chosen_cards):
        print(f"  - {expr}")
    print()
    print("Next: python3 export_apkg.py --release   # verifies the gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
