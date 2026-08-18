#!/bin/sh
set -eu

SOURCE_DIR=${1:-"/Users/joleen/Desktop/19. KISWAHILI STD III - Complete"}
OUTPUT_DIR=${2:-"content/i18n/sw/video"}

mkdir -p "$OUTPUT_DIR"

export OUTPUT_DIR
find "$SOURCE_DIR" -type f -iname '*.mp4' -exec sh -c '
  for source do
    number=$(basename "$source" | sed -E "s/[^0-9]*([0-9]+)\\.mp4/\\1/I")
    output=$(printf "%s/page_%03d.mp4" "$OUTPUT_DIR" "$number")
    [ -s "$output" ] && continue

    ffmpeg -y -v error -i "$source" \
      -map 0:v:0 -an \
      -vf "scale=640:-2:flags=lanczos" \
      -c:v libx264 -preset veryfast -crf 28 \
      -pix_fmt yuv420p -movflags +faststart \
      "$output"
  done
' sh {} +
