from pathlib import Path

from core import (
    clean_transcript,
    is_bilibili_url,
    parse_json_subtitle,
    parse_srt,
    parse_vtt,
    sanitize_filename,
    subtitle_file_to_text,
)


def test_is_bilibili_url() -> None:
    assert is_bilibili_url("https://www.bilibili.com/video/BV1xx411c7mD")
    assert is_bilibili_url("https://b23.tv/abc123")
    assert not is_bilibili_url("https://www.youtube.com/watch?v=demo")


def test_sanitize_filename() -> None:
    assert sanitize_filename('bad:/\\*?"<>|name') == "bad_name"


def test_parse_srt() -> None:
    text = """1
00:00:00,000 --> 00:00:01,000
你好

2
00:00:01,000 --> 00:00:02,000
世界
"""
    assert parse_srt(text) == "你好\n世界"


def test_parse_vtt() -> None:
    text = """WEBVTT

00:00.000 --> 00:01.000
Hello

00:01.000 --> 00:02.000
World
"""
    assert parse_vtt(text) == "Hello\nWorld"


def test_parse_json_subtitle() -> None:
    raw = '{"body": [{"content": "第一句"}, {"content": "第二句"}]}'
    assert parse_json_subtitle(raw) == "第一句\n第二句"


def test_clean_transcript() -> None:
    assert clean_transcript("<i>Hello</i>\nHello\n\nWorld") == "Hello\nWorld"


def test_subtitle_file_to_text(tmp_path: Path) -> None:
    path = tmp_path / "sample.srt"
    path.write_text("1\n00:00:00,000 --> 00:00:01,000\n你好\n", encoding="utf-8")
    assert subtitle_file_to_text(path) == "你好"
