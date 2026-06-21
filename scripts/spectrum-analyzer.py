#!/usr/bin/env python3
"""Render blindscan spectrum files as compact terminal plots."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_FILES = [
    Path("/tmp/spectrum_rf0_H.dat"),
    Path("/tmp/spectrum_rf0_V.dat"),
]


def read_points(path: Path) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
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


def render(path: Path, width: int) -> bool:
    if not path.exists():
        print(f"{path}: missing")
        return False

    points = read_points(path)
    if not points:
        print(f"{path}: empty")
        return False

    buckets = downsample(points, width)
    low = min(level for _, level in buckets)
    high = max(level for _, level in buckets)
    chars = " .:-=+*#%@"

    print()
    print(
        f"{path.name}: {points[0][0]:.1f}-{points[-1][0]:.1f} MHz, "
        f"strongest-bin level {low:.0f}..{high:.0f}"
    )

    if high == low:
        print(chars[0] * len(buckets))
    else:
        scale = len(chars) - 1
        print("".join(chars[int((level - low) / (high - low) * scale)] for _, level in buckets))

    print(f"left={buckets[0][0]:.1f} MHz  right={buckets[-1][0]:.1f} MHz")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render /tmp blindscan spectrum data as terminal analyzer bars."
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        default=DEFAULT_FILES,
        help="Spectrum .dat files to render. Defaults to /tmp/spectrum_rf0_H.dat and V.dat.",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=100,
        help="Plot width in characters. Default: 100.",
    )
    args = parser.parse_args()

    if args.width < 10:
        parser.error("--width must be at least 10")

    rendered = [render(path, args.width) for path in args.files]
    return 0 if any(rendered) else 1


if __name__ == "__main__":
    raise SystemExit(main())
