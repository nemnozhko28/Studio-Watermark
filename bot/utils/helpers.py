import os
import asyncio
import logging
from pathlib import Path
from bot.config import config

logger = logging.getLogger(__name__)


def get_file_size_mb(path: str) -> float:
    """Return file size in megabytes."""
    return os.path.getsize(path) / (1024 * 1024)


def get_file_size_str(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def get_video_format(filename: str) -> str:
    """Extract extension from filename."""
    return Path(filename).suffix.lstrip(".").lower()


def ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    for d in [config.temp_dir, config.fonts_dir, config.logs_dir]:
        Path(d).mkdir(parents=True, exist_ok=True)


def temp_path(filename: str) -> str:
    """Build a path inside the temp directory."""
    return os.path.join(config.temp_dir, filename)


async def safe_remove(path: str) -> None:
    """Remove a file without raising if it doesn't exist."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug(f"Removed temp file: {path}")
    except Exception as e:
        logger.warning(f"Could not remove {path}: {e}")


def sanitize_filename(name: str) -> str:
    """Remove characters that are unsafe for filenames."""
    keepchars = (" ", ".", "_", "-")
    return "".join(c for c in name if c.isalnum() or c in keepchars).strip()


def format_progress(current: int, total: int) -> str:
    """Return a text progress percentage."""
    if total == 0:
        return "0%"
    pct = int(current / total * 100)
    return f"{pct}%"


async def run_subprocess(cmd: list, timeout: int = 3600) -> tuple[int, str, str]:
    """Run a subprocess asynchronously and return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise TimeoutError(f"Subprocess timed out after {timeout}s: {' '.join(cmd)}")
