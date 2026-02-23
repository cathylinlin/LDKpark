#!/usr/bin/env python3
"""Select a representative subset of frames from a directory.

Default strategy: pick frames from 3 segments (start/middle/end) to preserve
visible state changes, then renumber them into a compact sequence.

Examples:
  # In-place: keep 30 frames (10 from start + 10 mid + 10 end)
  python3 scripts/select_frames.py assets/dinosaur/frames --pattern 'run_*.png'

  # Custom counts
  python3 scripts/select_frames.py assets/dinosaur/frames --pattern 'run_*.png' --start 8 --middle 12 --end 10

Notes:
- Only files matching --pattern are replaced.
- Output files are named: <prefix>_<000..>.png (default prefix: "run").
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class Selection:
    src_path: str
    src_index: int


def _evenly_pick_indices(n: int, k: int) -> list[int]:
    if k <= 0 or n <= 0:
        return []
    if n <= k:
        return list(range(n))
    if k == 1:
        return [n // 2]

    # Use linspace-like rounding; then de-duplicate while preserving order.
    raw = [int(round(i * (n - 1) / (k - 1))) for i in range(k)]
    seen: set[int] = set()
    idxs: list[int] = []
    for idx in raw:
        if idx not in seen:
            seen.add(idx)
            idxs.append(idx)

    # If rounding caused duplicates, fill the gaps by scanning neighbors.
    candidate = 0
    while len(idxs) < k and candidate < n:
        if candidate not in seen:
            seen.add(candidate)
            idxs.append(candidate)
        candidate += 1

    return idxs


def select_start_middle_end(paths: list[str], start: int, middle: int, end: int) -> list[Selection]:
    paths = list(paths)
    n = len(paths)
    if n == 0:
        return []

    third = max(1, n // 3)
    start_seg = paths[:third]
    mid_seg = paths[third : max(third + 1, 2 * third)]
    end_seg = paths[max(2 * third, 0) :]

    picked: list[Selection] = []

    def pick(seg: list[str], k: int, offset: int) -> None:
        idxs = _evenly_pick_indices(len(seg), k)
        for i in idxs:
            picked.append(Selection(seg[i], offset + i))

    pick(start_seg, start, 0)
    pick(mid_seg, middle, len(start_seg))
    pick(end_seg, end, len(start_seg) + len(mid_seg))

    # De-duplicate by src_index (shouldn't happen often, but be safe)
    uniq: dict[int, Selection] = {}
    for sel in picked:
        uniq.setdefault(sel.src_index, sel)

    return [uniq[i] for i in sorted(uniq.keys())]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("frames_dir", help="Directory containing frames")
    ap.add_argument("--pattern", default="run_*.png", help="Glob pattern within frames_dir")
    ap.add_argument("--start", type=int, default=10, help="How many to sample from the start segment")
    ap.add_argument("--middle", type=int, default=10, help="How many to sample from the middle segment")
    ap.add_argument("--end", type=int, default=10, help="How many to sample from the end segment")
    ap.add_argument("--prefix", default="run", help="Output filename prefix")
    ap.add_argument("--digits", type=int, default=3, help="Zero-padding digits for output numbering")
    args = ap.parse_args()

    frames_dir = os.path.abspath(args.frames_dir)
    if not os.path.isdir(frames_dir):
        raise SystemExit(f"Not a directory: {frames_dir}")

    paths = sorted(glob.glob(os.path.join(frames_dir, args.pattern)))
    if not paths:
        raise SystemExit(f"No frames matched: {os.path.join(frames_dir, args.pattern)}")

    selected = select_start_middle_end(paths, args.start, args.middle, args.end)
    if not selected:
        raise SystemExit("Selection is empty")

    tmp_dir = os.path.join(frames_dir, ".__tmp_selected__")
    os.makedirs(tmp_dir, exist_ok=True)

    # Copy selected frames into tmp, renumbered.
    out_paths: list[str] = []
    for i, sel in enumerate(selected):
        out_name = f"{args.prefix}_{i:0{args.digits}d}.png"
        out_path = os.path.join(tmp_dir, out_name)
        shutil.copy2(sel.src_path, out_path)
        out_paths.append(out_path)

    # Remove old matching frames and replace with selected set.
    for p in paths:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass

    for p in out_paths:
        shutil.move(p, os.path.join(frames_dir, os.path.basename(p)))

    try:
        os.rmdir(tmp_dir)
    except OSError:
        # non-empty or other issue; ignore
        pass

    print(f"total_matched={len(paths)} selected={len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
