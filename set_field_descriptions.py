#!/usr/bin/env python3
"""Set the field descriptions on the Chinese note type.

Split out of bootstrap_chinese_model.py so it is safe to re-run: field
NAMES are owned by the Anki UI (AGENTS.md rule 0), and this script only
writes the descriptive text shown in the Fields dialog. It changes
nothing an existing card depends on.

    python3 set_field_descriptions.py

Requires: Anki running with Anki-Connect.
"""
import json
import os
import sys
import urllib.request

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"

# name -> description. Only names that exist in the live model are
# touched, and only descriptions that actually differ are written, so a
# re-run is a no-op instead of a redundant collection save.
DESCRIPTIONS = {
    "Expression": "Term expressed, without inflections (Chinese has none), using the "
                  "maximal-character form actually seen in the sentence. Best field for "
                  "search and duplicate detection.",
    "Definition": "Mined glossary HTML (Yomitan). Compacted to 1 dictionary / 2 senses "
                  "on the card; the full version lives in Extended definition.",
    "Hanzi Notes": "Empty by default. Per-character information you deem necessary: "
                   "radicals, stroke counts, mnemonics, component words, confusable pairs.",
    "Source": "URL, show name, book name, etc.",
    "Sentence": "The mined sentence. Must be self-contained enough to solve the card on "
                "its own (PRODUCT.md: front sentence = self-contained learning unit).",
    "Sentence Pinyin": "Pinyin of the Sentence, tone-marked or numeric. Shown as a quiet "
                       "second line under the sentence on the back card.",
    "Translation": "English translation of the sentence; literal wording is welcome.",
    "context": "The whole paragraph/dialogue. Typically from books, added manually.",
    "Notes": "Everything else: grammar, other word definitions.",
    "Pinyin": "Tone-marked Pinyin of the Expression (e.g. chuáng). This is the reading "
              "the learner is testing; the template colors the four tones.",
    "cloze-body": "Original term as it appeared before Yomitan reduced it to dictionary "
                  "form. Chinese is unaffected by inflection, so this equals Expression "
                  "for most cards; it is the second identity discriminator for the Mature "
                  "Word Mode content search.",
    "Frequency": "Frequency rank of the cloze body.",
    "Extended definition": "Full mined glossary. Shown only behind 详情.",
}


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
    names = _anki("modelFieldNames", modelName=MODEL_NAME)
    current = _anki("modelFieldDescriptions", modelName=MODEL_NAME) or [""] * len(names)
    if len(current) != len(names):
        current = [""] * len(names)

    written, skipped, unknown = 0, 0, []
    for name, desc in DESCRIPTIONS.items():
        if name not in names:
            unknown.append(name)
            continue
        if current[names.index(name)] == desc:
            skipped += 1
            continue
        _anki("modelFieldSetDescription", modelName=MODEL_NAME, fieldName=name, description=desc)
        written += 1
        print(f"  set description: {name}")

    print(f"descriptions: {written} written, {skipped} already correct")
    if unknown:
        print(f"WARNING: not present in the live model (rename them in the Anki UI): "
              f"{', '.join(unknown)}")


if __name__ == "__main__":
    main()
