from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    import yt_dlp  # type: ignore
except ImportError:  # pragma: no cover
    yt_dlp = None


LogFn = Callable[[str], None]


class ExtractionError(Exception):
    pass


@dataclass
class ExtractResult:
    title: str
    video_id: str
    source: str
    transcript_text: str
    raw_subtitle_path: Optional[str] = None
    audio_path: Optional[str] = None
    transcript_path: Optional[str] = None


SUPPORTED_EXTS = {".srt", ".vtt", ".json", ".txt"}
AUDIO_EXTS = {".m4a", ".mp3", ".webm", ".wav", ".mp4", ".aac", ".flac", ".ogg", ".opus"}
DEFAULT_LANGS = "zh.*,zh-CN,zh-Hans,zh-Hant,en.*"


def ensure_dependency() -> None:
    if yt_dlp is None:
        raise ExtractionError("缺少 yt-dlp。请先运行: pip install yt-dlp")


def is_bilibili_url(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False
    return "bilibili.com" in host or "b23.tv" in host


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120] or "video"


def parse_langs(lang_text: str) -> List[str]:
    return [item.strip() for item in lang_text.split(",") if item.strip()]


def choose_best_file(candidates: Iterable[Path]) -> Optional[Path]:
    ranked: List[tuple[int, Path]] = []
    for path in candidates:
        score = 0
        suffix = path.suffix.lower()
        if suffix == ".srt":
            score += 4
        elif suffix == ".vtt":
            score += 3
        elif suffix == ".json":
            score += 2
        elif suffix == ".txt":
            score += 1
        ranked.append((score, path))
    if not ranked:
        return None
    ranked.sort(key=lambda x: (x[0], x[1].stat().st_size if x[1].exists() else 0), reverse=True)
    return ranked[0][1]


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_srt(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        lines.append(line)
    return clean_transcript("\n".join(lines))


def parse_vtt(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("WEBVTT") or upper.startswith("NOTE"):
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    return clean_transcript("\n".join(lines))


def parse_json_subtitle(text: str) -> str:
    data = json.loads(text)
    body = data.get("body") if isinstance(data, dict) else None
    if isinstance(body, list):
        joined = "\n".join(
            str(item.get("content", "")).strip()
            for item in body
            if isinstance(item, dict) and str(item.get("content", "")).strip()
        )
        return clean_transcript(joined)
    if isinstance(data, dict):
        for key in ("text", "content", "transcript"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return clean_transcript(value)
    raise ExtractionError("字幕 JSON 格式无法识别。")


def subtitle_file_to_text(path: Path) -> str:
    raw = _read_text(path)
    suffix = path.suffix.lower()
    if suffix == ".srt":
        return parse_srt(raw)
    if suffix == ".vtt":
        return parse_vtt(raw)
    if suffix == ".json":
        return parse_json_subtitle(raw)
    return clean_transcript(raw)


def clean_transcript(text: str) -> str:
    lines = []
    last = None
    for raw in text.splitlines():
        line = re.sub(r"<[^>]+>", "", raw)
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        if line == last:
            continue
        lines.append(line)
        last = line
    return "\n".join(lines).strip()


def download_url_to_file(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f)


def fetch_info(url: str, cookiefile: Optional[str] = None) -> dict:
    ensure_dependency()
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[attr-defined]
        info = ydl.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise ExtractionError("无法读取视频信息。")
    return info


def _matches_any_lang(lang: str, preferred_langs: List[str]) -> bool:
    return any(
        re.fullmatch(pattern.replace("*", ".*"), lang) or re.search(pattern, lang)
        for pattern in preferred_langs
    )


def try_direct_subtitle_from_info(
    info: dict,
    output_dir: Path,
    preferred_langs: List[str],
    log: LogFn,
) -> Optional[Path]:
    candidates = []
    for source_name in ("subtitles", "automatic_captions"):
        source = info.get(source_name)
        if not isinstance(source, dict):
            continue
        for lang, entries in source.items():
            if isinstance(entries, list):
                for item in entries:
                    if not isinstance(item, dict):
                        continue
                    subtitle_url = item.get("url")
                    ext = item.get("ext") or "json"
                    if subtitle_url:
                        candidates.append(
                            (lang, ext, subtitle_url, source_name, _matches_any_lang(lang, preferred_langs))
                        )
    if not candidates:
        return None

    def lang_score(lang: str, matched: bool) -> int:
        score = 50 if matched else 0
        for idx, pattern in enumerate(preferred_langs):
            regex = pattern.replace("*", ".*")
            if re.fullmatch(regex, lang) or re.search(regex, lang):
                score = max(score, 100 - idx)
        if lang.startswith("zh"):
            score += 20
        elif lang.startswith("en"):
            score += 10
        return score

    def ext_score(ext: str) -> int:
        mapping = {"srt": 4, "vtt": 3, "json": 2, "txt": 1}
        return mapping.get(ext.lower(), 0)

    candidates.sort(
        key=lambda item: (lang_score(item[0], item[4]), ext_score(item[1]), 1 if item[3] == "subtitles" else 0),
        reverse=True,
    )
    lang, ext, sub_url, source_name, _matched = candidates[0]
    safe_title = sanitize_filename(str(info.get("title") or info.get("id") or "video"))
    out_path = output_dir / f"{safe_title}.{lang}.{ext}"
    log(f"找到{source_name}：{lang} ({ext})")
    download_url_to_file(sub_url, out_path)
    return out_path


def try_download_subtitle_with_ytdlp(
    url: str,
    output_dir: Path,
    preferred_langs: List[str],
    cookiefile: Optional[str],
    log: LogFn,
) -> Optional[Path]:
    ensure_dependency()
    before = set(output_dir.rglob("*"))
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": preferred_langs,
        "subtitlesformat": "srt/vtt/best",
        "paths": {"home": str(output_dir), "subtitle": str(output_dir)},
        "outtmpl": {"default": "%(title).80s [%(id)s].%(ext)s"},
        "compat_opts": ["no-live-chat"],
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[attr-defined]
            ydl.download([url])
    except Exception as exc:
        log(f"yt-dlp 直接下载字幕失败：{exc}")
        return None
    after = set(output_dir.rglob("*"))
    new_files = [p for p in after - before if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    return choose_best_file(new_files)


def download_audio(
    url: str,
    output_dir: Path,
    cookiefile: Optional[str],
    log: LogFn,
) -> Path:
    ensure_dependency()
    before = set(output_dir.rglob("*"))
    opts = {
        "format": "bestaudio/best",
        "paths": {"home": str(output_dir)},
        "outtmpl": {"default": "%(title).80s [%(id)s].%(ext)s"},
        "quiet": True,
        "no_warnings": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[attr-defined]
        ydl.download([url])
    after = set(output_dir.rglob("*"))
    new_files = [p for p in after - before if p.is_file() and p.suffix.lower() in AUDIO_EXTS]
    chosen = choose_best_file(new_files)
    if not chosen:
        raise ExtractionError("音频下载完成，但没有找到音频文件。")
    log(f"音频已下载：{chosen.name}")
    return chosen


def transcribe_audio(
    audio_path: Path,
    model_size: str,
    device: str,
    log: LogFn,
) -> str:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise ExtractionError("缺少 faster-whisper。请先运行: pip install faster-whisper") from exc

    compute_type = "int8"
    actual_device = device
    if device == "auto":
        try:
            import torch  # type: ignore

            actual_device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            actual_device = "cpu"

    if actual_device == "cuda":
        compute_type = "float16"

    log(f"开始加载模型：model={model_size}, device={actual_device}, compute_type={compute_type}")
    model = WhisperModel(model_size, device=actual_device, compute_type=compute_type)
    log("模型加载完成，开始转写。首次运行可能需要更久。")

    segments, info = model.transcribe(str(audio_path), vad_filter=True)
    chunks: List[str] = []
    for idx, seg in enumerate(segments, start=1):
        text = seg.text.strip()
        if text:
            chunks.append(text)
        if idx % 20 == 0:
            log(f"转写中：已处理约 {idx} 个片段...")

    text = "\n".join(chunks)
    if not text.strip():
        raise ExtractionError("转写结果为空。")
    lang = getattr(info, "language", "unknown")
    prob = getattr(info, "language_probability", None)
    if prob is not None:
        log(f"检测语言：{lang} (置信度 {prob:.2f})")
    else:
        log(f"检测语言：{lang}")
    return clean_transcript(text)


def save_transcript(output_dir: Path, title: str, text: str) -> Path:
    safe_title = sanitize_filename(title)
    out = output_dir / f"{safe_title}.transcript.txt"
    out.write_text(text, encoding="utf-8")
    return out


def extract_bilibili_transcript(
    url: str,
    output_dir: str,
    preferred_langs: str = DEFAULT_LANGS,
    transcribe_when_needed: bool = True,
    whisper_model: str = "small",
    device: str = "auto",
    cookiefile: Optional[str] = None,
    log: Optional[LogFn] = None,
) -> ExtractResult:
    log = log or (lambda msg: None)
    if not url.strip():
        raise ExtractionError("请先输入视频链接。")
    if not is_bilibili_url(url):
        raise ExtractionError("当前这个工具只处理 B 站链接。")

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    langs = parse_langs(preferred_langs or DEFAULT_LANGS)

    log("读取视频信息...")
    info = fetch_info(url, cookiefile=cookiefile)
    title = str(info.get("title") or "Bilibili Video")
    video_id = str(info.get("id") or "unknown")
    log(f"标题：{title}")
    log(f"视频 ID：{video_id}")

    subtitle_path = try_direct_subtitle_from_info(info, out_dir, langs, log)
    if subtitle_path is None:
        log("没有直接拿到字幕链接，尝试让 yt-dlp 下载字幕...")
        subtitle_path = try_download_subtitle_with_ytdlp(url, out_dir, langs, cookiefile, log)

    if subtitle_path and subtitle_path.exists():
        text = subtitle_file_to_text(subtitle_path)
        transcript_path = save_transcript(out_dir, title, text)
        log(f"字幕提取完成：{subtitle_path.name}")
        return ExtractResult(
            title=title,
            video_id=video_id,
            source="subtitle",
            transcript_text=text,
            raw_subtitle_path=str(subtitle_path),
            transcript_path=str(transcript_path),
        )

    if not transcribe_when_needed:
        raise ExtractionError("没有找到可用字幕，且你关闭了自动转写。")

    log("没有找到可用字幕，开始下载音频并转写...")
    audio_path = download_audio(url, out_dir, cookiefile, log)
    text = transcribe_audio(audio_path, whisper_model, device, log)
    transcript_path = save_transcript(out_dir, title, text)
    log("语音转写完成。")
    return ExtractResult(
        title=title,
        video_id=video_id,
        source="whisper",
        transcript_text=text,
        audio_path=str(audio_path),
        transcript_path=str(transcript_path),
    )
