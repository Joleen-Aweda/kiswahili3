#!/usr/bin/env python3
"""Remove all standalone quizzes and repair the ADT navigation indexes."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "content" / "pages.json"
LANGUAGES = ("sw", "sw-TZ")
SECTION_INDEX = re.compile(
    r'(<meta\s+name=["\']page-section-id["\']\s+content=["\'])\d+(["\']\s*/?>)',
    re.IGNORECASE,
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    pages = json.loads(PAGES_PATH.read_text(encoding="utf-8"))
    quizzes = [entry for entry in pages if str(entry.get("section_id", "")).startswith("qz")]
    remaining = [entry for entry in pages if entry not in quizzes]
    if not quizzes:
        print("No quizzes found; navigation indexes are already quiz-free.")
        return

    for index, entry in enumerate(remaining, start=1):
        html_path = ROOT / entry["href"]
        source = html_path.read_text(encoding="utf-8")
        updated, replacements = SECTION_INDEX.subn(rf"\g<1>{index}\g<2>", source, count=1)
        if replacements != 1:
            raise RuntimeError(f"Expected one page-section-id in {html_path.name}")
        html_path.write_text(updated, encoding="utf-8")

    write_json(PAGES_PATH, remaining)

    deleted_audio = 0
    deleted_entries = 0
    for language in LANGUAGES:
        base = ROOT / "content" / "i18n" / language
        texts_path = base / "texts.json"
        audios_path = base / "audios.json"
        texts = json.loads(texts_path.read_text(encoding="utf-8"))
        audios = json.loads(audios_path.read_text(encoding="utf-8"))
        quiz_audio = {key: filename for key, filename in audios.items() if key.startswith("qz")}
        for filename in set(quiz_audio.values()):
            audio_path = base / "audio" / filename
            if audio_path.exists():
                audio_path.unlink()
                deleted_audio += 1
        cleaned_texts = {key: value for key, value in texts.items() if not key.startswith("qz")}
        cleaned_audios = {key: value for key, value in audios.items() if not key.startswith("qz")}
        deleted_entries += (len(texts) - len(cleaned_texts)) + (len(audios) - len(cleaned_audios))
        write_json(texts_path, cleaned_texts)
        write_json(audios_path, cleaned_audios)

    for entry in quizzes:
        quiz_path = ROOT / entry["href"]
        if quiz_path.exists():
            quiz_path.unlink()

    print(
        f"Removed {len(quizzes)} quizzes, {deleted_entries} localization mappings, "
        f"and {deleted_audio} audio files; reindexed {len(remaining)} pages."
    )


if __name__ == "__main__":
    main()
