#!/usr/bin/env python3
"""Generate the complete ADT read-aloud corpus in Tanzanian Swahili."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import edge_tts


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LANGUAGE = "sw-TZ"
TARGET_LANGUAGES = ("sw", "sw-TZ")
VOICE = "sw-TZ-RehemaNeural"

ONES = (
    "sifuri", "moja", "mbili", "tatu", "nne", "tano", "sita", "saba",
    "nane", "tisa", "kumi", "kumi na moja", "kumi na mbili", "kumi na tatu",
    "kumi na nne", "kumi na tano", "kumi na sita", "kumi na saba",
    "kumi na nane", "kumi na tisa",
)
TENS = (
    "", "", "ishirini", "thelathini", "arobaini", "hamsini", "sitini",
    "sabini", "themanini", "tisini",
)
MONTHS = {
    1: "Januari", 2: "Februari", 3: "Machi", 4: "Aprili", 5: "Mei",
    6: "Juni", 7: "Julai", 8: "Agosti", 9: "Septemba", 10: "Oktoba",
    11: "Novemba", 12: "Desemba",
}

SWAHILI_LETTER_NAMES = {
    "a": "a", "b": "be", "c": "che", "d": "de", "e": "e",
    "f": "fe", "g": "ge", "h": "ha", "i": "i", "j": "je",
    "k": "ka", "l": "le", "m": "me", "n": "ne", "o": "o",
    "p": "pe", "q": "ku", "r": "re", "s": "se", "t": "te",
    "u": "u", "v": "ve", "w": "we", "x": "ksi", "y": "ye",
    "z": "ze",
}

ROMAN_VALUES = {
    "i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000,
}


def number_to_swahili(value: int) -> str:
    if value < 0:
        return f"hasi {number_to_swahili(-value)}"
    if value < 20:
        return ONES[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return TENS[tens] + (f" na {ONES[ones]}" if ones else "")
    if value < 1_000:
        hundreds, rest = divmod(value, 100)
        return f"mia {ONES[hundreds]}" + (f" na {number_to_swahili(rest)}" if rest else "")
    if value < 1_000_000:
        thousands, rest = divmod(value, 1_000)
        prefix = "elfu moja" if thousands == 1 else f"elfu {number_to_swahili(thousands)}"
        return prefix + (f" na {number_to_swahili(rest)}" if rest else "")
    millions, rest = divmod(value, 1_000_000)
    prefix = "milioni moja" if millions == 1 else f"milioni {number_to_swahili(millions)}"
    return prefix + (f" na {number_to_swahili(rest)}" if rest else "")


def digits_in_swahili(value: str) -> str:
    return " ".join(ONES[int(character)] for character in value if character.isdigit())


def year_in_swahili(value: int) -> str:
    return number_to_swahili(value)


def roman_to_integer(value: str) -> int:
    total = 0
    previous = 0
    for character in reversed(value.lower()):
        current = ROMAN_VALUES[character]
        total += -current if current < previous else current
        previous = max(previous, current)
    return total


def normalize_number_and_letter_markers(text: str) -> str:
    """Expand textbook list markers for natural Tanzanian Swahili narration."""
    text = re.sub(
        r"^\s*\(?([ivx]+)\)?[.)]?(?:\s+|$)",
        lambda match: f"Namba {number_to_swahili(roman_to_integer(match.group(1)))}. ",
        text,
    )
    text = re.sub(
        r"^\s*\(?([A-Za-z])\)?[.)]\s*",
        lambda match: f"Herufi {SWAHILI_LETTER_NAMES[match.group(1).lower()]}. ",
        text,
    )
    text = re.sub(
        r"(?<![\w])(?<!Herufi )(?<!herufi )([A-Za-z])(?![\w])",
        lambda match: f"herufi {SWAHILI_LETTER_NAMES[match.group(1).lower()]}",
        text,
    )
    return text


def spoken_text(text_id: str, visible: str) -> str:
    """Return narration text without changing the visible textbook content."""
    text = str(visible).strip()
    if not text:
        return ""

    symbol_only = re.sub(r"[\s()]", "", text)
    if not symbol_only:
        return "mabano"
    if symbol_only and set(symbol_only) <= set(".,!?/"):
        names = {".": "nukta", ",": "koma", "!": "mshangao", "?": "kiulizo", "/": "mstari mshazari"}
        return ", ".join(names[character] for character in symbol_only)

    text = re.sub(r"https?://ol\.tie\.go\.tz|\bol\.tie\.go\.tz\b", "maktaba mtandao ya Taasisi ya Elimu Tanzania", text, flags=re.I)
    text = re.sub(r"\bwww\.tie\.go\.tz\b", "tovuti ya Taasisi ya Elimu Tanzania", text, flags=re.I)
    text = re.sub(r"\bFOR ONLINE READING ONLY\b", "Kwa kusoma mtandaoni pekee", text, flags=re.I)
    text = re.sub(r"\bTET\b", "Taasisi ya Elimu Tanzania", text)
    text = re.sub(r"\bISBN\b", "namba ya kitabu", text, flags=re.I)
    text = re.sub(r"\bS\.\s*L\.\s*P\.", "Sanduku la Posta", text, flags=re.I)
    text = re.sub(r"\bQR\b", "mrejesho wa haraka", text, flags=re.I)
    text = re.sub(r"\bHR\b", "nakala bora", text)
    text = re.sub(r"\bTRIAL\b", "majaribio", text, flags=re.I)
    text = re.sub(r"\bToleo la Pili\b", "Toleo la pili", text)
    text = re.sub(r"\.indd\b", "", text, flags=re.I)
    text = re.sub(r"\[\[blank[^]]*\]\]", " nafasi wazi ", text, flags=re.I)
    text = re.sub(r"_{3,}|\.{4,}|…{2,}", " ", text, flags=re.I)
    text = normalize_number_and_letter_markers(text)

    # Dates and clock times are expanded before generic slash/operator handling.
    def date_replacement(match: re.Match[str]) -> str:
        day, month, year = map(int, match.groups())
        month_name = MONTHS.get(month, number_to_swahili(month))
        return f"tarehe {number_to_swahili(day)} {month_name}, mwaka {year_in_swahili(year)}"

    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", date_replacement, text)
    text = re.sub(
        r"\b(\d{1,2}):(\d{2})\b",
        lambda match: f"saa {number_to_swahili(int(match.group(1)))} na dakika {number_to_swahili(int(match.group(2)))}",
        text,
    )

    # ISBNs and phone numbers should be spoken digit-by-digit, using Swahili digits.
    text = re.sub(
        r"(?<!\w)(?:\+?\d[\d -]{7,}\d)(?!\w)",
        lambda match: digits_in_swahili(match.group(0)),
        text,
    )

    # Four-digit publication years are read as complete Swahili numbers.
    text = re.sub(
        r"\b(?:19|20)\d{2}\b",
        lambda match: year_in_swahili(int(match.group(0))),
        text,
    )

    # Numbered exercise markers receive an explicit Swahili cue.
    text = re.sub(
        r"^\s*(\d{1,3})[.)]\s*",
        lambda match: f"Namba {number_to_swahili(int(match.group(1)))}. ",
        text,
    )
    text = re.sub(
        r"(?<![\w])\d{1,7}(?:,\d{3})*(?![\w])",
        lambda match: number_to_swahili(int(match.group(0).replace(",", ""))),
        text,
    )

    replacements = {
        "×": " zidisha kwa ", "÷": " gawanya kwa ", "=": " ni sawa na ",
        "+": " jumlisha ", "%": " asilimia ", "–": " hadi ", "—": " hadi ",
    }
    for symbol, words in replacements.items():
        text = text.replace(symbol, words)
    text = re.sub(r"\s/\s", " au ", text)
    text = re.sub(r"(?<=\w)/(?=\w)", " au ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return text


def load_jobs() -> tuple[dict[str, list[Path]], dict[str, str]]:
    source_root = ROOT / "content" / "i18n" / SOURCE_LANGUAGE
    texts = json.loads((source_root / "texts.json").read_text(encoding="utf-8"))
    mappings = json.loads((source_root / "audios.json").read_text(encoding="utf-8"))
    for text_id, visible in texts.items():
        if str(visible).strip():
            mappings.setdefault(text_id, f"{text_id}.mp3")

    for language in TARGET_LANGUAGES:
        mapping_path = ROOT / "content" / "i18n" / language / "audios.json"
        mapping_path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    grouped: dict[str, list[Path]] = defaultdict(list)
    for text_id, filename in mappings.items():
        speech = spoken_text(text_id, texts.get(text_id, ""))
        if not speech:
            continue
        for language in TARGET_LANGUAGES:
            grouped[speech].append(ROOT / "content" / "i18n" / language / "audio" / filename)
    return grouped, mappings


async def run(args: argparse.Namespace) -> None:
    jobs, mappings = load_jobs()
    items = sorted(jobs.items())
    if args.numbers_and_letters_only:
        texts = json.loads(
            (ROOT / "content" / "i18n" / SOURCE_LANGUAGE / "texts.json").read_text(encoding="utf-8")
        )
        selected = {
            text_id for text_id, visible in texts.items()
            if re.search(r"\d", str(visible))
            or re.match(r"^\s*\(?[ivx]+\)?[.)]?(?:\s+|$)", str(visible))
            or re.match(r"^\s*\(?[A-Za-z]\)?[.)]", str(visible))
            or re.search(r"(?<![\w])[A-Za-z](?![\w])", str(visible))
        }
        items = [
            (speech, destinations) for speech, destinations in items
            if any(destination.stem in selected for destination in destinations)
        ]
    if args.filename:
        selected = set(args.filename)
        items = [
            (speech, destinations) for speech, destinations in items
            if any(destination.stem in selected for destination in destinations)
        ]
    if args.limit:
        items = items[:args.limit]
    print(f"Mapped {len(mappings)} tracks; selected {len(items)} unique phrases with {VOICE}")
    if args.dry_run:
        for speech, destinations in items[: args.show]:
            print(destinations[0].name, "=>", speech)
        return

    cache_root = Path(tempfile.mkdtemp(prefix="kiswahili-rehema-"))
    semaphore = asyncio.Semaphore(args.workers)
    failures: list[tuple[str, str]] = []
    completed = 0

    async def generate(speech: str, destinations: list[Path]) -> None:
        nonlocal completed
        digest = hashlib.sha256(speech.encode("utf-8")).hexdigest()
        cached = cache_root / f"{digest}.mp3"
        temporary = cached.with_suffix(".tmp")
        try:
            async with semaphore:
                for attempt in range(1, args.retries + 1):
                    try:
                        await asyncio.wait_for(
                            edge_tts.Communicate(speech, VOICE, rate=args.rate).save(str(temporary)),
                            timeout=args.timeout,
                        )
                        if temporary.stat().st_size < 300:
                            raise RuntimeError("speech service returned an invalid MP3")
                        temporary.replace(cached)
                        break
                    except Exception:
                        temporary.unlink(missing_ok=True)
                        if attempt == args.retries:
                            raise
                        await asyncio.sleep(min(2 ** attempt, 8))
            for destination in destinations:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(cached, destination)
            completed += 1
            if completed % 250 == 0:
                print(f"Completed {completed}/{len(items)} unique phrases", flush=True)
        except Exception as exc:
            failures.append((destinations[0].name, str(exc)))

    try:
        await asyncio.gather(*(generate(speech, destinations) for speech, destinations in items))
    finally:
        shutil.rmtree(cache_root, ignore_errors=True)

    print(f"Generated {completed}/{len(items)} unique phrases; failures={len(failures)}")
    for filename, error in failures[:50]:
        print(f"{filename}: {error}", file=sys.stderr)
    if failures:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--rate", default="-5%")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--filename", action="append", help="generate a specific audio filename stem")
    parser.add_argument(
        "--numbers-and-letters-only",
        action="store_true",
        help="regenerate only tracks containing digits, Roman numerals, or isolated letters",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show", type=int, default=100)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
