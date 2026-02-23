#!/usr/bin/env python3
"""Extract frames from a GIF into a frames directory.

Usage:
    python scripts/gif_to_frames.py <gif-path> <out-dir> [--prefix run_]

Requires: Pillow (pip install Pillow)
"""
import sys
import os
from PIL import Image, ImageSequence


def extract(gif_path, out_dir, prefix="frame_"):
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(gif_path)
    count = 0
    for i, frame in enumerate(ImageSequence.Iterator(im)):
        frame = frame.convert("RGBA")
        out_path = os.path.join(out_dir, f"{prefix}{i:03d}.png")
        frame.save(out_path)
        count += 1
    print(f"Extracted {count} frames to {out_dir}")


def main(argv):
    if len(argv) < 3:
        print("Usage: gif_to_frames.py <gif-path> <out-dir> [--prefix run_]")
        return 2
    gif, out = argv[1], argv[2]
    prefix = "frame_"
    if len(argv) >= 4:
        prefix = argv[3]
    extract(gif, out, prefix)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
