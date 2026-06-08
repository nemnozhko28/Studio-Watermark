import os
import logging
import json
from pathlib import Path
from typing import Optional, Callable, Awaitable
from bot.config import FONTS, POSITIONS, config
from bot.utils import run_subprocess, safe_remove

logger = logging.getLogger(__name__)


def _parse_size_percent(size_str: str) -> float:
    """Convert '6%' -> 6.0"""
    return float(size_str.rstrip("%"))


def _get_ffmpeg_position_expr(position: str, offset_x: int = 0, offset_y: int = 0) -> tuple[str, str]:
    """
    Returns (x_expr, y_expr) FFmpeg drawtext expressions for a given position.
    offset_x and offset_y are pixel offsets.
    """
    margin = 20
    ox = f"+{offset_x}" if offset_x >= 0 else str(offset_x)
    oy = f"+{offset_y}" if offset_y >= 0 else str(offset_y)

    exprs = {
        "left_top":       (f"{margin}{ox}", f"{margin}{oy}"),
        "center_top":     (f"(w-text_w)/2{ox}", f"{margin}{oy}"),
        "right_top":      (f"w-text_w-{margin}{ox}", f"{margin}{oy}"),
        "left_center":    (f"{margin}{ox}", f"(h-text_h)/2{oy}"),
        "center":         (f"(w-text_w)/2{ox}", f"(h-text_h)/2{oy}"),
        "right_center":   (f"w-text_w-{margin}{ox}", f"(h-text_h)/2{oy}"),
        "left_bottom":    (f"{margin}{ox}", f"h-text_h-{margin}{oy}"),
        "center_bottom":  (f"(w-text_w)/2{ox}", f"h-text_h-{margin}{oy}"),
        "right_bottom":   (f"w-text_w-{margin}{ox}", f"h-text_h-{margin}{oy}"),
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
    """Build a single FFmpeg drawtext filter string."""
    # Escape special chars for drawtext
    safe_text = text.replace("'", "\\'").replace(":", "\\:")

    x_expr, y_expr = _get_ffmpeg_position_expr(position, offset_x, offset_y)

    # Convert opacity (0.0-1.0) to hex alpha (00-FF)
    alpha_hex = format(int(opacity * 255), "02X")
    font_color = f"{color}@{opacity}"

    # fontsize = size_pct% of video width
    fontsize_expr = f"w*{size_pct / 100}"

    drawtext = (
        f"drawtext="
        f"fontfile='{font_path}':"
        f"text='{safe_text}':"
        f"fontcolor={font_color}:"
        f"fontsize={fontsize_expr}:"
        f"x={x_expr}:"
        f"y={y_expr}:"
        f"enable='{enable_expr}'"
    )
    return drawtext


def build_watermark_filter(settings) -> str:
    """
    Build the complete FFmpeg video filter string for the watermark.
    Handles both single-position and alternation modes.
    """
    font_path = FONTS.get(settings.font, FONTS["Montserrat-Bold"])
    size_pct = _parse_size_percent(settings.size)
    text = settings.text or "Watermark"
    color = settings.color
    opacity = float(settings.opacity)

    if not settings.alternation_enabled or not settings.alternation_json:
        # Simple single-position watermark
        drawtext = _build_drawtext_filter(
            text=text,
            font_path=font_path,
            size_pct=size_pct,
            color=color,
            opacity=opacity,
            position=settings.position,
        )
        return drawtext

    # Alternation mode
    alt_data = settings.alternation_json
    interval = int(alt_data.get("interval", 5))
    positions = alt_data.get("positions", [])

    if not positions:
        # Fallback to single position
        drawtext = _build_drawtext_filter(
            text=text,
            font_path=font_path,
            size_pct=size_pct,
            color=color,
            opacity=opacity,
            position=settings.position,
        )
        return drawtext

    drawtext_filters = []
    for i, pos_data in enumerate(positions):
        pos_key = pos_data.get("position", "right_bottom")
        ox = int(pos_data.get("offset_x", 0))
        oy = int(pos_data.get("offset_y", 0))

        # Time windows: position i is active during [i*interval, (i+1)*interval), repeating
        # Using modulo: floor(t/interval) % n_positions == i
        n = len(positions)
        enable_expr = f"eq(mod(floor(t/{interval}),{n}),{i})"

        dt = _build_drawtext_filter(
            text=text,
            font_path=font_path,
            size_pct=size_pct,
            color=color,
            opacity=opacity,
            position=pos_key,
            offset_x=ox,
            offset_y=oy,
            enable_expr=enable_expr,
        )
        drawtext_filters.append(dt)

    # Chain multiple drawtext filters
    return ",".join(drawtext_filters)


SYSTEM_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def _resolve_font(font_name: str) -> str:
    """
    Resolve a font name to an absolute path.
    Priority: bot/fonts/ directory → system fonts.
    Never returns a non-existent path.
    """
    # 1. Check configured bot font path
    configured = FONTS.get(font_name)
    if configured and os.path.exists(configured):
        return configured

    # 2. Check all bot font files regardless of name
    for path in FONTS.values():
        if os.path.exists(path):
            logger.info(f"Font '{font_name}' not found, using '{path}' instead")
            return path

    # 3. Fall back to system fonts
    for candidate in SYSTEM_FONT_CANDIDATES:
        if os.path.exists(candidate):
            logger.info(f"Using system font fallback: {candidate}")
            return candidate

    raise FileNotFoundError(
        "No usable font file found. "
        "Run scripts/download_fonts.sh or ensure fonts-dejavu-core is installed."
    )


async def apply_watermark(
    input_path: str,
    output_path: str,
    settings,
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    """
    Apply watermark using FFmpeg. Streams processing without loading into RAM.
    Calls progress_callback with percentage strings during processing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Resolve font — guaranteed to return a valid path or raise clearly
    font_path = _resolve_font(settings.font)

    filter_str = build_watermark_filter(settings)

    # Get video duration for progress tracking
    duration = await _get_video_duration(input_path)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        "-progress", "pipe:1",
        output_path,
    ]

    logger.info(f"Running FFmpeg: {' '.join(cmd[:6])} ...")

    proc = __import__("asyncio").create_subprocess_exec

    import asyncio
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    last_reported = -1
    stderr_chunks = []

    async def read_progress():
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

    async def read_stderr():
        data = await process.stderr.read()
        stderr_chunks.append(data.decode())

    await asyncio.gather(read_progress(), read_stderr())
    returncode = await process.wait()

    if returncode != 0:
        stderr_output = "".join(stderr_chunks)
        logger.error(f"FFmpeg failed (rc={returncode}):\n{stderr_output[-2000:]}")
        raise RuntimeError(f"FFmpeg error (code {returncode}): {stderr_output[-500:]}")

    if progress_callback:
        await progress_callback("100%")

    logger.info(f"Watermark applied successfully: {output_path}")


async def _get_video_duration(path: str) -> Optional[float]:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        rc, stdout, stderr = await run_subprocess(cmd, timeout=30)
        if rc == 0 and stdout.strip():
            return float(stdout.strip())
    except Exception as e:
        logger.warning(f"Could not get duration for {path}: {e}")
    return None


async def get_video_info(path: str) -> dict:
    """Return basic video metadata: duration, width, height, format."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
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
