#!/usr/bin/env bash
# Generate Latin-range SDF glyph PBFs from a TTF and commit them to the repo.
#
# Usage:
#   ./scripts/generate_glyphs.sh "<fontstack-name>" "<ttf-url>"
#
# Examples:
#   ./scripts/generate_glyphs.sh "Bebas Neue Regular" \
#       "https://fonts.gstatic.com/s/bebasneue/v16/JTUSjIg69CK48gW7PXooxW4.ttf"
#
#   ./scripts/generate_glyphs.sh "Poiret One Regular" \
#       "$(curl -fsSL 'https://fonts.googleapis.com/css2?family=Poiret+One&display=swap' \
#           | grep -o 'https://fonts.gstatic.com[^)]*')"
#
# Output: src/static/glyphs/<fontstack-name>/{0-255,256-511,512-767,8192-8447}.pbf
# Kept ranges cover Basic Latin, Latin Extended A/B, and General Punctuation.
#
# Requires: build_pbf_glyphs (cargo install build_pbf_glyphs), curl

set -euo pipefail

FONTSTACK="${1:?Usage: $0 \"<fontstack-name>\" \"<ttf-url>\"}"
TTF_URL="${2:?Usage: $0 \"<fontstack-name>\" \"<ttf-url>\"}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$REPO_ROOT/src/static/glyphs/$FONTSTACK"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

BUILD_PBF=$(command -v build_pbf_glyphs || echo "$HOME/.cargo/bin/build_pbf_glyphs")
if [[ ! -x "$BUILD_PBF" ]]; then
    echo "ERROR: build_pbf_glyphs not found. Install with: cargo install build_pbf_glyphs" >&2
    exit 1
fi

echo "Downloading TTF..."
mkdir -p "$WORK/input"
curl -fsSL "$TTF_URL" -o "$WORK/input/font.ttf"

echo "Generating PBFs..."
mkdir -p "$WORK/output"
"$BUILD_PBF" "$WORK/input" "$WORK/output"

GENERATED=$(find "$WORK/output" -mindepth 1 -maxdepth 1 -type d | head -1)
if [[ -z "$GENERATED" ]]; then
    echo "ERROR: build_pbf_glyphs produced no output directory" >&2
    exit 1
fi

echo "Pruning to Latin + punctuation ranges..."
mkdir -p "$DEST"
for RANGE in "0-255" "256-511" "512-767" "8192-8447"; do
    if [[ -f "$GENERATED/$RANGE.pbf" ]]; then
        cp "$GENERATED/$RANGE.pbf" "$DEST/$RANGE.pbf"
        echo "  $RANGE.pbf ($(wc -c < "$DEST/$RANGE.pbf") bytes)"
    else
        echo "  WARNING: $RANGE.pbf not found — font may not cover this range"
    fi
done

echo ""
echo "Done: $DEST"
echo "Total: $(du -sh "$DEST" | cut -f1)"
echo ""
echo "Next: git add \"$DEST\" && git commit -m \"Add $FONTSTACK glyphs\""
