#!/usr/bin/env python3
"""One-shot bootstrap: create the Chinese note type + sample deck in Anki.

Run once, by hand, from the repo root:

    python3 bootstrap_chinese_model.py

It is deliberately NOT part of ./verify or finish.sh:
  - fields are owned by the Anki UI (AGENTS.md rule 0), so the repo
    contains no static field list — this script carries the names only
    for the initial creation and is kept in git purely as a record of
    what was created;
  - the note type is NOT tracked by any release flow. Templates + CSS
    reach Anki through sync_to_anki.py (which snapshots whatever is live
    into backups/ first, so a hand-run never silently overwrites work).
  - a second run is refused: re-creating a live note type would be
    destructive. Use the Anki UI to change fields.

Requires: Anki running with Anki-Connect.
"""
import json
import os
import sys
import urllib.request

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"
DECK_NAME = "My Life Decks::Chinese"

# (name, description) in the order they appear in the note editor.
FIELDS = [
    ("Expression", "Term expressed, without inflections (Chinese has none), using the "
                   "maximal-character form actually seen in the sentence. Best field for "
                   "search and duplicate detection."),
    ("Definition", "Mined glossary HTML (Yomitan). Compacted to 1 dictionary / 2 senses "
                   "on the card; the full version lives in Extended definition."),
    ("Hanzi Notes", "Empty by default. Per-character information you deem necessary: "
                   "radicals, stroke counts, mnemonics, component words, confusable pairs."),
    ("Source", "URL, show name, book name, etc."),
    ("Sentence", "The mined sentence. Must be self-contained enough to solve the card "
                 "on its own (see PRODUCT.md: front sentence = self-contained unit)."),
    ("Sentence Pinyin", "Pinyin of the Sentence, tone-marked or numeric. Shown as a "
                        "quiet second line under the sentence on the back card."),
    ("Sentence Audio", ""),
    ("Translation", "English translation of the sentence; literal wording is welcome."),
    ("Picture", ""),
    ("context", "The whole paragraph/dialogue. Typically from books, added manually."),
    ("Notes", "Everything else: grammar, other word definitions."),
    ("Word Audio", ""),
    ("Pinyin", "Tone-marked Pinyin of the Expression (e.g. chu\u00e1ng). This is the "
               "reading the learner is testing; the template colors the four tones."),
    ("cloze-prefix", ""),
    ("cloze-body", "Original term as it appeared before Yomitan reduced it to dictionary "
                   "form. Chinese is unaffected by inflection, so this equals Expression "
                   "for most cards; it is the second identity discriminator for the "
                   "Mature Word Mode content search."),
    ("cloze-suffix", ""),
    ("Frequency", "Frequency rank of the cloze body."),
    ("Extended definition", "Full mined glossary. Shown only behind 详情."),
]

FRONT_STUB = "{{FrontSide}}\n\n<!-- bootstrap placeholder: replaced by sync_to_anki.py -->"
BACK_STUB = "{{FrontSide}}\n\n<!-- bootstrap placeholder: replaced by sync_to_anki.py -->"


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
    existing = _anki("modelNames")
    if MODEL_NAME in existing:
        print(f"REFUSING: model '{MODEL_NAME}' already exists. Change fields in the Anki "
              "UI; this script is create-only.")
        sys.exit(1)

    model = _anki(
        "createModel",
        modelName=MODEL_NAME,
        inOrderFields=[name for name, _ in FIELDS],
        css="/* replaced by sync_to_anki.py */",
        isCloze=False,
        # This Anki-Connect build wants cardTemplates as dicts carrying
        # Name/Front/Back. The stubs only have to exist: sync_to_anki.py
        # replaces both templates and the CSS on the first ./finish.sh run.
        cardTemplates=[{"Name": "Card 1", "Front": FRONT_STUB, "Back": BACK_STUB}],
    )
    # createModel returns the raw Anki model dict (keys: name, flds, tmpls).
    print(f"model: created '{model['name']}' with {len(model['flds'])} fields")

    for name, desc in FIELDS:
        if not desc:
            continue
        try:
            _anki("modelFieldSetDescription", modelName=MODEL_NAME, fieldName=name, description=desc)
        except Exception as e:  # older Anki-Connect builds lack the action
            print(f"  (warning: could not set description for '{name}': {e})")

    deck = _anki("createDeck", deck=DECK_NAME)
    print(f"deck: ready '{deck}'")

    print()
    print("Fields created:")
    for i, (name, desc) in enumerate(FIELDS):
        print(f"  {i:2d}. {name}")
    print()
    print("Next: ./finish.sh \"feat: initial Chinese note type\"  (or --local while iterating)")
    print("It runs ./verify, stamps the version, pushes templates+CSS into Anki,")
    print("exports dist/anki-chinese-template.apkg, and commits.")


if __name__ == "__main__":
    main()
