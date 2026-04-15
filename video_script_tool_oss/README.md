# bili-script-tool

Extract transcripts from **Bilibili videos** with a simple desktop GUI and CLI.

The extraction strategy is deliberately pragmatic:

1. Try official or auto subtitles first.
2. If no subtitle is available, download audio.
3. Run local Whisper transcription as fallback.

This project is designed for people who want usable text quickly, not a giant media pipeline.

## Features

- Subtitle-first extraction for faster results
- Local Whisper fallback when subtitles are missing
- Simple Windows desktop GUI
- CLI for automation and scripting
- Saves clean transcript text to `*.transcript.txt`
- Optional cookies support for login-only videos

## Screenshot

The GUI includes:

- Bilibili URL input
- Output directory picker
- Optional cookies file
- Subtitle language priority
- Whisper model and device selection
- Live logs and transcript output

## Quick start

### Option 1: run from source

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt
python app.py
```

### Option 2: use the CLI

```bash
pip install -r requirements.txt
python cli.py "https://www.bilibili.com/video/BV..."
```

Or after installation:

```bash
bili-script "https://www.bilibili.com/video/BV..."
```

## Packaging for Windows

Recommended:

```bat
build_exe.bat
```

Output:

```text
dist\BiliTranscriptTool\BiliTranscriptTool.exe
```

Single-file variant:

```bat
build_onefile.bat
```

Output:

```text
dist\BiliTranscriptTool.exe
```

## CLI examples

Basic:

```bash
python cli.py "https://www.bilibili.com/video/BV..."
```

Specify output folder and model:

```bash
python cli.py "https://www.bilibili.com/video/BV..." -o outputs --model small --device cpu
```

Disable transcription fallback:

```bash
python cli.py "https://www.bilibili.com/video/BV..." --no-transcribe
```

Use cookies:

```bash
python cli.py "https://www.bilibili.com/video/BV..." --cookie-file cookies.txt
```

## Development

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

Lint:

```bash
ruff check .
```

## Project structure

```text
.
├── app.py
├── cli.py
├── core.py
├── tests/
├── .github/
├── build_exe.bat
├── build_onefile.bat
├── pyproject.toml
└── README_zh.md
```

## Roadmap

- Add YouTube extractor
- Add batch queue support
- Add Markdown / JSON export
- Add better progress feedback during long CPU transcriptions
- Add plugin-style platform adapters

## Open source notes

This repository is prepared to be published directly on GitHub. It includes:

- MIT license
- contribution guide
- code of conduct
- security policy
- issue templates
- pull request template
- basic CI for tests and linting

## Chinese README

See [`README_zh.md`](README_zh.md).

## Disclaimer

Use this tool responsibly and comply with the terms of service, copyright rules, and local laws that apply to the media you process.
