#!/usr/bin/env python3
"""Live terminal waterfall for STiD135 spectrum scans."""

from __future__ import annotations

import argparse
import shutil
import statistics
import subprocess
import sys
import time
from collections import deque
from pathlib import Path


CHARS = " .:-=+*#%@"
BLOCKS = " ▁▂▃▄▅▆▇█"
COLORS = [
    "\033[38;5;235m",
    "\033[38;5;24m",
    "\033[38;5;31m",
    "\033[38;5;38m",
    "\033[38;5;46m",
    "\033[38;5;226m",
    "\033[38;5;208m",
    "\033[38;5;196m",
    "\033[1;38;5;196m",
]
RESET = "\033[0m"
DEFAULT_TOOL = "stid135-blindscan"


def read_points(path: Path) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if not path.exists():
        return points

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if len(fields) < 2:
                continue
            try:
                points.append((float(fields[0]), float(fields[1])))
            except ValueError:
                continue
    return points


def downsample(points: list[tuple[float, float]], width: int) -> list[tuple[float, float]]:
    if len(points) <= width:
        return points

    bucket_size = len(points) / width
    buckets: list[tuple[float, float]] = []
    for bucket in range(width):
        start = int(bucket * bucket_size)
        end = int((bucket + 1) * bucket_size)
        chunk = points[start:end] or points[start : start + 1]
        freq = sum(point[0] for point in chunk) / len(chunk)
        level = max(point[1] for point in chunk)
        buckets.append((freq, level))
    return buckets


def level_index(level: float, low: float, high: float, scale: int) -> int:
    if high == low:
        return 0
    return max(0, min(scale, int((level - low) / (high - low) * scale)))


def marker_index(buckets: list[tuple[float, float]], freq: float) -> int:
    distances = [abs(bucket_freq - freq) for bucket_freq, _ in buckets]
    return distances.index(min(distances))


def render_row(
    buckets: list[tuple[float, float]], target_freq: float | None, color: bool
) -> tuple[str, float, float, float, list[tuple[float, float]], float | None]:
    levels = [level for _, level in buckets]
    low = min(levels)
    high = max(levels)
    median = statistics.median(levels)
    peak_freq = buckets[levels.index(high)][0]
    target_level = None
    target_idx = None
    if target_freq is not None:
        target_idx = marker_index(buckets, target_freq)
        target_level = buckets[target_idx][1]

    scale = len(BLOCKS) - 1
    chars: list[str] = []
    for idx, (_, level) in enumerate(buckets):
        if target_idx is not None and idx == target_idx:
            chars.append(f"\033[1;97;45m│{RESET}" if color else "|")
            continue
        char_idx = level_index(level, low, high, scale)
        char = BLOCKS[char_idx]
        if color:
            color_idx = min(char_idx, len(COLORS) - 1)
            char = f"{COLORS[color_idx]}{char}{RESET}"
        chars.append(char)

    top_levels = sorted(buckets, key=lambda item: item[1], reverse=True)[:5]
    return "".join(chars), high, median, peak_freq, top_levels, target_level


def spectrum_path(rf_in: int, pol: str) -> Path:
    return Path(f"/tmp/spectrum_rf{rf_in}_{pol}.dat")


def run_scan(args: argparse.Namespace, path: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        DEFAULT_TOOL,
        "-c",
        "blindscan",
        "-a",
        str(args.adapter),
        "--rf-in",
        str(args.rf_in),
        "-s",
        str(args.start_freq),
        "-e",
        str(args.end_freq),
        "-p",
        args.pol,
        "--spectrum-method",
        "fft",
        "--spectral-resolution",
        str(args.spectral_resolution),
        args.lnb,
    ]
    if args.sudo:
        cmd = ["sudo", "-n", *cmd]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size > 0:
            time.sleep(0.1)
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
        time.sleep(0.1)

    process.terminate()
    try:
        stdout, stderr = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    return subprocess.CompletedProcess(cmd, 124, stdout, stderr)


def remove_old_spectrum(path: Path, use_sudo: bool) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except PermissionError:
        if not use_sudo:
            raise
        subprocess.run(
            ["sudo", "-n", "rm", "-f", str(path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )


def terminal_size(args: argparse.Namespace) -> tuple[int, int]:
    size = shutil.get_terminal_size((120, 32))
    width = args.width or min(max(size.columns - 2, 40), 160)
    height = args.rows or max(size.lines - 8, 8)
    return width, height


def print_screen(
    rows: deque[str],
    args: argparse.Namespace,
    sample: int,
    high: float | None,
    median: float | None,
    peak_freq: float | None,
    target_level: float | None,
    top_levels: list[tuple[float, float]],
    best_high: float | None,
    best_contrast: float | None,
    message: str,
) -> None:
    print("\033[2J\033[H", end="")
    print(
        f"Live waterfall A{args.adapter}/rf{args.rf_in} {args.pol} "
        f"{args.start_freq / 1000:.1f}-{args.end_freq / 1000:.1f} MHz "
        f"sample={sample}"
    )
    if high is None or median is None or peak_freq is None:
        print("Waiting for spectrum data...")
    else:
        contrast = high - median
        best_high_text = "n/a" if best_high is None else f"{best_high:.0f}"
        best_contrast_text = "n/a" if best_contrast is None else f"{best_contrast:.0f}"
        target_text = "n/a"
        if args.target_freq is not None and target_level is not None:
            target_text = f"{args.target_freq / 1000:.1f} MHz level={target_level:.0f}"
        peak_offset = ""
        if args.target_freq is not None:
            peak_offset = f" offset={peak_freq - args.target_freq / 1000:+.1f} MHz"
        print(
            f"peak={high:.0f} median={median:.0f} contrast={contrast:.0f} "
            f"peak_freq={peak_freq:.1f} MHz{peak_offset} best_peak={best_high_text} "
            f"best_contrast={best_contrast_text}"
        )
        print(f"target={target_text}")
        if top_levels:
            peaks = "  ".join(f"{freq:.1f}:{level:.0f}" for freq, level in top_levels)
            print(f"top bins {peaks}")
    print("left=low freq, right=high freq. Colored blocks mark stronger bins. Ctrl-C exits.")
    if message:
        print(message[: shutil.get_terminal_size((120, 32)).columns - 1])
    print("-" * max(len(rows[0]) if rows else 40, 40))
    for row in rows:
        print(row)
    sys.stdout.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Live terminal waterfall for dish aiming.")
    parser.add_argument("-a", "--adapter", type=int, default=1)
    parser.add_argument("-r", "--rf-in", type=int, default=3)
    parser.add_argument("-p", "--pol", choices=["H", "V"], default="H")
    parser.add_argument("-s", "--start-freq", type=int, default=11820000, help="Start frequency in kHz.")
    parser.add_argument("-e", "--end-freq", type=int, default=11870000, help="End frequency in kHz.")
    parser.add_argument("--lnb", choices=["universal", "wideband", "wideband-uk", "C"], default="universal")
    parser.add_argument("--spectral-resolution", type=int, default=100)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--rows", type=int, default=0)
    parser.add_argument(
        "--target-freq",
        type=int,
        default=11842000,
        help="Target frequency in kHz. Use 0 to disable the marker.",
    )
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--no-sudo", dest="sudo", action="store_false")
    parser.set_defaults(sudo=True)
    args = parser.parse_args()

    width, height = terminal_size(args)
    rows: deque[str] = deque(maxlen=height)
    sample = 0
    best_high: float | None = None
    best_contrast: float | None = None
    path = spectrum_path(args.rf_in, args.pol)
    target_freq = None if args.target_freq == 0 else args.target_freq / 1000

    try:
        while True:
            sample += 1
            remove_old_spectrum(path, args.sudo)

            result = run_scan(args, path)
            points = read_points(path)
            message = ""
            high = median = peak_freq = None
            target_level = None
            top_levels: list[tuple[float, float]] = []

            if points:
                row, high, median, peak_freq, top_levels, target_level = render_row(
                    downsample(points, width), target_freq, not args.no_color
                )
                rows.append(row)
                contrast = high - median
                best_high = high if best_high is None else max(best_high, high)
                best_contrast = contrast if best_contrast is None else max(best_contrast, contrast)
            else:
                rows.append("?" * width)
                if result.returncode == 124:
                    message = "scan timed out before writing spectrum data"
                else:
                    message = "scan did not write spectrum data"

            if result.returncode not in (0, 124):
                message = (result.stderr or result.stdout).strip().replace("\n", " ")

            print_screen(
                rows,
                args,
                sample,
                high,
                median,
                peak_freq,
                target_level,
                top_levels,
                best_high,
                best_contrast,
                message,
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
