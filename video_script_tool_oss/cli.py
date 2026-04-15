from __future__ import annotations

import argparse
from pathlib import Path

from core import DEFAULT_LANGS, ExtractionError, extract_bilibili_transcript


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract transcript text from a Bilibili video.")
    parser.add_argument("url", help="Bilibili video URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=str((Path.cwd() / "outputs").resolve()),
        help="Directory to save outputs",
    )
    parser.add_argument(
        "--langs", default=DEFAULT_LANGS, help="Preferred subtitle language patterns, comma-separated"
    )
    parser.add_argument("--cookie-file", default=None, help="Optional Netscape-format cookies file")
    parser.add_argument("--no-transcribe", action="store_true", help="Disable fallback audio transcription")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model",
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Compute device")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    def log(msg: str) -> None:
        print(msg, flush=True)

    try:
        result = extract_bilibili_transcript(
            url=args.url,
            output_dir=args.output_dir,
            preferred_langs=args.langs,
            transcribe_when_needed=not args.no_transcribe,
            whisper_model=args.model,
            device=args.device,
            cookiefile=args.cookie_file,
            log=log,
        )
    except ExtractionError as exc:
        print(f"ERROR: {exc}")
        return 1

    print("\n--- transcript ---\n")
    print(result.transcript_text)
    if result.transcript_path:
        print(f"\nSaved to: {result.transcript_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
