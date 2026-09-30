#!/usr/bin/env python3
"""One-shot: seed `My Life Decks::Chinese` with sample cards.

Run once, by hand, from the repo root:

    python3 seed_sample_cards.py

WHY THIS EXISTS
---------------
`exportPackage` on an **empty** deck does not export an empty apkg — Anki
falls back to the Default deck and ships the wrong note types. The release
notes already tell users to "import the apkg, then delete the sample
cards", which only works if the deck is non-empty. So the deck ships a
handful of representative cards.

They are ordinary notes in the ordinary deck, tagged `anki-chinese-template-sample`
so `Browse → tag:…` finds them. Delete them any time; the note type and
the deck survive.

Each note exercises one real branch of the templates, so a fresh install is
also a smoke test of front modes, the compactor, Pinyin tones and the
listening front.

Requires: Anki running with Anki-Connect.
"""
import json
import os
import sys
import urllib.request

ANKI_CONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Chinese Note type (Sentence card by Default)"
DECK_NAME = "My Life Decks::Chinese"
SAMPLE_TAG = "anki-chinese-template-sample"

GLOSSARY = (
    '<div style="text-align: left;" class="yomitan-glossary"><ol>'
    '<li data-dictionary="CC-CEDICT"><span>'
    '<ul data-sc-content="glossary">'
    '<li>to study; to learn</li>'
    '<li>study; learning</li>'
    '<li>THIS THIRD SENSE IS COMPACTED AWAY</li>'
    '</ul></span></li>'
    '<li data-dictionary="MDBG"><span>THIS SECOND DICTIONARY IS HIDDEN</span></li>'
    '</ol></div>'
)

# One note per interesting front/back shape. Fields are the live model's
# field order (see .anki_fields.json); a wrong name here is a hard error
# from Anki, not a silent blank.
NOTES = [
    {
        "tags": SAMPLE_TAG,
        "Expression": "学习",
        "Definition": GLOSSARY,
        "Hanzi Notes": "<b>习</b> — 羽 over 白; the image is a bird learning to fly. "
                       "Pair with <b>學</b> (traditional).",
        "Source": "CC-CEDICT (sample)",
        "Sentence": "他每天<strong>学习</strong>两个小时中文，从来没有间断过。",
        "Sentence Pinyin": "tā měi tiān xué xí liǎng gè xiǎoshí zhōngwén, cóng lái méi yǒu duàn jié guò.",
        "Sentence Audio": "",
        "Translation": "He studies Chinese for two hours every day and has never once let up.",
        "Picture": "",
        "context": "他每天<strong>学习</strong>两个小时中文，从来没有间断过。",
        "Notes": "学习 also names the schooling system itself ( schooling / education ).",
        "Word Audio": "",
        "Pinyin": "xué xí",
        "cloze-prefix": "他每天",
        "cloze-body": "学习",
        "cloze-suffix": "两个小时",
        "Frequency": "1200",
        "Extended definition": "<div class='yomitan-glossary'><ol><li><ul data-sc-content='glossary'>"
                               "<li>to learn; to study; to imitate (a model)</li>"
                               "<li>learning; study; schooling</li>"
                               "<li>to learn from; take one's cue from</li>"
                               "</ul></li></ol></div>",
    },
    {
        "tags": SAMPLE_TAG,
        "Expression": "窗户",
        "Definition": (
            '<div style="text-align: left;" class="yomitan-glossary"><ol>'
            '<li data-dictionary="CC-CEDICT"><span>'
            '<ul data-sc-content="glossary">'
            '<li>window (of a building)</li>'
            '<li>an opening in a wall or roof that admits light or air</li>'
            '</ul></span></li></ol></div>'
        ),
        "Hanzi Notes": "",
        "Source": "CC-CEDICT (sample)",
        "Sentence": "他把<strong>窗户</strong>打开，外面的冷空气一下子涌了进来。",
        "Sentence Pinyin": "tā bǎ chuāng hu dǎ kāi, wài miàn de lěng kōng qì yí xià yǒng le jìn lái.",
        "Sentence Audio": "",
        "Translation": "He opened the window, and the cold air from outside rushed in.",
        "Picture": "",
        "context": "",
        "Notes": "",
        "Word Audio": "",
        "Pinyin": "chuāng hu",
        "cloze-prefix": "他把",
        "cloze-body": "窗户",
        "cloze-suffix": "打开",
        "Frequency": "3400",
        "Extended definition": "",
    },
    {
        # Listening card: no Definition, no Frequency, no Extended
        # definition — only audio. Exercises the classic audio-only front.
        "tags": [SAMPLE_TAG, "listening"],
        "Expression": "图书馆",
        "Definition": "",
        "Hanzi Notes": "",
        "Source": "CC-CEDICT (sample)",
        "Sentence": "图书馆晚上九点关门。",
        "Sentence Pinyin": "tú shū guǎn wǎn shang jiǔ diǎn guān mén.",
        "Sentence Audio": "",
        "Translation": "The library closes at nine in the evening.",
        "Picture": "",
        "context": "",
        "Notes": "",
        "Word Audio": "",
        "Pinyin": "tú shū guǎn",
        "cloze-prefix": "",
        "cloze-body": "图书馆",
        "cloze-suffix": "",
        "Frequency": "",
        "Extended definition": "",
    },
]


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
    field_names = _anki("modelFieldNames", modelName=MODEL_NAME)
    # `tags` is note metadata, not a field — everything else must be a real
    # field name, or Anki would silently write into the wrong column.
    unknown = set()
    for note in NOTES:
        unknown |= set(note) - set(field_names) - {"tags"}
    if unknown:
        print(f"ERROR: these fields are not in the live model: {sorted(unknown)}")
        print(f"       live model fields: {field_names}")
        sys.exit(1)

    existing = _anki("findNotes", query=f'"tag:{SAMPLE_TAG}"')
    if existing:
        print(f"refusing: {len(existing)} note(s) already carry the {SAMPLE_TAG} tag.")
        print("Delete them in Anki first, or edit this script — re-adding would duplicate.")
        sys.exit(1)

    added = 0
    for note in NOTES:
        # This Anki-Connect build wants `fields` as a name→value MAPPING
        # (createNote iterates note['fields'].items() and matches names
        # case-insensitively). A list is rejected.
        fields = {name: str(note.get(name, "")) for name in field_names}
        note_id = _anki("addNote", note={
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": fields,
            "tags": [note["tags"]] if isinstance(note["tags"], str) else note["tags"],
            "options": {"allowDuplicate": False},
        })
        if note_id is None:
            print(f"  skipped (duplicate): {note['Expression']}")
        else:
            added += 1
            print(f"  added: {note['Expression']}  ({note_id})")

    cards = _anki("findCards", query=f'"tag:{SAMPLE_TAG}"')
    print(f"sample cards in '{DECK_NAME}': {len(cards)} ({added} added now)")
    print()
    print("These exist so exportPackage has something to export and so a fresh")
    print("install is a smoke test. Delete them whenever: note type + deck stay.")
    print()
    print("Next: ./finish.sh \"chore: seed sample cards\"")
    print("(tag the release; the apkg is rebuilt from the deck.)")


if __name__ == "__main__":
    main()
