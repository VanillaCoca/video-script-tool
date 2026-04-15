# Contributing

Thanks for considering a contribution.

## Ground rules

- Keep the scope tight.
- Prefer simple, reviewable changes.
- Do not add large abstractions before they are needed.
- For platform support, discuss the extractor boundary before adding a new site.

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -U pip
pip install -r requirements-dev.txt
```

## Before opening a PR

Run:

```bash
ruff check .
pytest
```

## Pull requests

Please include:

- what changed
- why it changed
- screenshots if the GUI changed
- a note on any user-facing behavior change

## Feature requests

For major additions such as YouTube, Xiaohongshu, queue systems, or installer support, open an issue first.
