import os
import logging
import json
from pathlib import Path
from typing import Optional, Callable, Awaitable
from bot.config import FONTS, POSITIONS, config
from bot.utils import run_subprocess, safe_remove

logger = logging.getLogger(__name__)

# ─── Size mapping ─────────────────────────────────────────────────────────────
# Maps user-facing size label → % of video width for FFmpeg drawtext fontsize.
# This makes watermarks scale correctly across different video resolutions.
_SIZE_TO_PCT: dict[str, float] = {
    "10": 1.5,
    "12": 2.0,
    "14": 2.5,
    "16": 3.0,
    "18": 3.5,
    "20": 4.0,
    "24": 5.0,
    "28": 6.0,
    "32": 7.5,
    "36": 9.0,
    "48": 12.0,
    "64": 16.0,
    # Legacy percentage format — backward-compat with old DB records
    "2%":  2.0,  "4%":  4.0,  "6%":  6.0,  "8%":  8.0,
    "10%": 10.0, "12%": 12.0, "15%": 15.0, "20%": 20.0,
}


def _parse_size(size_str: str) -> float:
    """Return % of video width for the given size label."""
    if size_str in _SIZE_TO_PCT:
        return _SIZE_TO_PCT[size_str]
    # Fallback: try stripping '%' for legacy values
    try:
        return float(size_str.rstrip("%"))
    except ValueError:
        return 5.0  # safe default


def _parse_opacity(opacity_val) -> float:
    """
    Convert stored opacity to 0.0–1.0 float.
    DB stores 0.0–1.0; new percent strings like '80' are also handled.
    """
    try:
        v = float(opacity_val)
        if v > 1.0:
            return v / 100.0  # treat as percentage
        return v
    except (TypeError, ValueError):
        return 0.8


def _get_ffmpeg_position_expr(position: str, offset_x: int = 0, offset_y: int = 0) -> tuple[str, str]:
    margin = 20
    ox = f"+{offset_x}" if offset_x >= 0 else str(offset_x)
    oy = f"+{offset_y}" if offset_y >= 0 else str(offset_y)

    exprs = {
        "left_top":      (f"{margin}{ox}",          f"{margin}{oy}"),
        "center_top":    (f"(w-text_w)/2{ox}",      f"{margin}{oy}"),
        "right_top":     (f"w-text_w-{margin}{ox}", f"{margin}{oy}"),
        "left_center":   (f"{margin}{ox}",           f"(h-text_h)/2{oy}"),
        "center":        (f"(w-text_w)/2{ox}",       f"(h-text_h)/2{oy}"),
        "right_center":  (f"w-text_w-{margin}{ox}",  f"(h-text_h)/2{oy}"),
        "left_bottom":   (f"{margin}{ox}",            f"h-text_h-{margin}{oy}"),
        "center_bottom": (f"(w-text_w)/2{ox}",        f"h-text_h-{margin}{oy}"),
        "right_bottom":  (f"w-text_w-{margin}{ox}",   f"h-text_h-{margin}{oy}"),
    }
    return exprs.get(position, (f"{margin}", f"{margin}"))


def _build_drawtext_filter(
    text: str,
    font_path: str,
    size_pct: float,
    color: str,
    opacity: float,
    position: str,
    offset_x: int = 0,
    offset_y: int = 0,
    enable_expr: str = "1",
) -> str:
    safe_text = text.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
    x_expr, y_expr = _get_ffmpeg_position_expr(position, offset_x, offset_y)
    font_color = f"{color}@{opacity:.2f}"
    fontsize_expr = f"w*{size_pct / 100:.4f}"

    return (
        f"drawtext="
        f"fontfile='{font_path}':"
        f"text='{safe_text}':"
        f"fontcolor={font_color}:"
        f"fontsize={fontsize_expr}:"
        f"x={x_expr}:"
        f"y={y_expr}:"
        f"enable='{enable_expr}'"
    )


def build_watermark_filter(settings) -> str:
    font_path = _resolve_font(settings.font)
    size_pct = _parse_size(settings.size)
    opacity = _parse_opacity(settings.opacity)
    text = settings.text or "Watermark"
    color = settings.color

    delay = int(getattr(settings, "delay_seconds", 0))
    base_enable = f"gte(t,{delay})" if delay > 0 else "1"

    if not settings.alternation_enabled or not settings.alternation_json:
        return _build_drawtext_filter(
            text=text, font_path=font_path, size_pct=size_pct,
            color=color, opacity=opacity, position=settings.position,
            enable_expr=base_enable,
        )

    alt_data = settings.alternation_json
    interval = int(alt_data.get("interval", 5))
    positions = alt_data.get("positions", [])

    if not positions:
        return _build_drawtext_filter(
            text=text, font_path=font_path, size_pct=size_pct,
            color=color, opacity=opacity, position=settings.position,
            enable_expr=base_enable,
        )

    n = len(positions)
    filters = []
    for i, pos_data in enumerate(positions):
        pos_key = pos_data.get("position", "right_bottom")
        ox = int(pos_data.get("offset_x", 0))
        oy = int(pos_data.get("offset_y", 0))

        if delay > 0:
            alt_expr = f"eq(mod(floor((t-{delay})/{interval}),{n}),{i})"
            enable_expr = f"gte(t,{delay})*{alt_expr}"
        else:
            enable_expr = f"eq(mod(floor(t/{interval}),{n}),{i})"

        filters.append(_build_drawtext_filter(
            text=text, font_path=font_path, size_pct=size_pct,
            color=color, opacity=opacity, position=pos_key,
            offset_x=ox, offset_y=oy, enable_expr=enable_expr,
        ))

    return ",".join(filters)


SYSTEM_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def _resolve_font(font_name: str) -> str:
    configured = FONTS.get(font_name)
    if configured and os.path.exists(configured):
        return configured

    for path in FONTS.values():
        if os.path.exists(path):
            logger.info(f"Font '{font_name}' not found, using '{path}' instead")
            return path

    for candidate in SYSTEM_FONT_CANDIDATES:
        if os.path.exists(candidate):
            logger.info(f"Using system font fallback: {candidate}")
            return candidate

    raise FileNotFoundError(
        "No usable font found. Run scripts/download_fonts.sh"
    )


async def generate_thumbnail(video_path: str, thumb_path: str, time_sec: float = 1.0) -> Optional[str]:
    """Extract a single JPEG frame at time_sec for use as video thumbnail."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        "-vf", "scale=320:-2",
        thumb_path,
    ]
    try:
        rc, _, stderr = await run_subprocess(cmd, timeout=30)
        if rc == 0 and os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
            return thumb_path
        logger.warning(f"Thumbnail generation failed (rc={rc}): {stderr[:200]}")
    except Exception as exc:
        logger.warning(f"generate_thumbnail error: {exc}")
    return None


async def apply_watermark(
    input_path: str,
    output_path: str,
    settings,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")

    _resolve_font(settings.font)  # fail early with a clear message
    filter_str = build_watermark_filter(settings)
    duration = await _get_video_duration(input_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "ultrafast",   # fastest encode (fix #7)
        "-crf", "23",              # slight quality trade-off for speed
        "-threads", "0",           # use all CPU cores (fix #7)
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        output_path,
    ]

    logger.info(f"FFmpeg start: {' '.join(cmd[:6])} ...")

    import asyncio
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    last_reported = -1
    stderr_chunks: list[bytes] = []

    async def read_progress() -> None:
        nonlocal last_reported
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            text = line.decode().strip()
            if text.startswith("out_time_ms="):
                try:
                    ms = int(text.split("=")[1])
                    current_sec = ms / 1_000_000
                    if duration and duration > 0:
                        pct = min(int(current_sec / duration * 100), 99)
                        if pct != last_reported and pct % 5 == 0:
                            last_reported = pct
                            if progress_callback:
                                await progress_callback(f"{pct}%")
                except Exception:
                    pass

    async def read_stderr() -> None:
        data = await process.stderr.read()
        stderr_chunks.append(data)

    await asyncio.gather(read_progress(), read_stderr())
    returncode = await process.wait()

    if returncode != 0:
        stderr_output = b"".join(stderr_chunks).decode()
        logger.error(f"FFmpeg failed (rc={returncode}):\n{stderr_output[-2000:]}")
        raise RuntimeError(f"FFmpeg error (code {returncode}): {stderr_output[-500:]}")

    if progress_callback:
        await progress_callback("100%")

    logger.info(f"Watermark applied: {output_path}")


async def _get_video_duration(path: str) -> Optional[float]:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        rc, stdout, _ = await run_subprocess(cmd, timeout=30)
        if rc == 0 and stdout.strip():
            return float(stdout.strip())
    except Exception as exc:
        logger.warning(f"Could not get duration for {path}: {exc}")
    return None


async def get_video_info(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_streams", "-show_format",
        path,
    ]
    rc, stdout, stderr = await run_subprocess(cmd, timeout=30)
    if rc != 0:
        raise RuntimeError(f"ffprobe failed: {stderr[:500]}")
    data = json.loads(stdout)
    info = {"format": data.get("format", {}).get("format_name", "unknown")}
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            info["width"] = stream.get("width", 0)
            info["height"] = stream.get("height", 0)
            info["duration"] = float(data.get("format", {}).get("duration", 0))
            break
    return info
