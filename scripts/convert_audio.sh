#!/usr/bin/env bash
# Convert audio files (m4a -> ogg) using ffmpeg.
# Usage: ./scripts/convert_audio.sh input.m4a output.ogg

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <input.m4a> <output.ogg>"
  exit 2
fi
INPUT="$1"
OUTPUT="$2"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg not found. Install ffmpeg to use this script."
  exit 3
fi

ffmpeg -y -i "$INPUT" -c:a libvorbis -q:a 5 "$OUTPUT"
echo "Converted $INPUT -> $OUTPUT"
