#!/usr/bin/env bash
# Download required fonts for the watermark bot.
# Run this once during local setup: bash scripts/download_fonts.sh

set -e

FONTS_DIR="bot/fonts"
mkdir -p "$FONTS_DIR"

echo "Downloading fonts..."

# Montserrat Bold
if [ ! -f "$FONTS_DIR/Montserrat-Bold.ttf" ]; then
    wget -q \
      "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf" \
      -O "$FONTS_DIR/Montserrat-Bold.ttf" \
      && echo "✅ Montserrat-Bold downloaded" \
      || echo "⚠️  Montserrat-Bold failed, will use system fallback"
fi

# Roboto Regular
if [ ! -f "$FONTS_DIR/Roboto-Regular.ttf" ]; then
    wget -q \
      "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf" \
      -O "$FONTS_DIR/Roboto-Regular.ttf" \
      && echo "✅ Roboto-Regular downloaded" \
      || echo "⚠️  Roboto-Regular failed, will use system fallback"
fi

# Arial — use DejaVu Sans Bold as a free substitute
if [ ! -f "$FONTS_DIR/Arial.ttf" ]; then
    # Try system copy first
    for candidate in \
        /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
        /usr/share/fonts/TTF/DejaVuSans-Bold.ttf; do
        if [ -f "$candidate" ]; then
            cp "$candidate" "$FONTS_DIR/Arial.ttf"
            echo "✅ Arial (DejaVu fallback) copied from $candidate"
            break
        fi
    done
    if [ ! -f "$FONTS_DIR/Arial.ttf" ]; then
        echo "⚠️  Arial fallback not found — will use system default"
    fi
fi

echo ""
echo "Font setup complete. Contents of $FONTS_DIR:"
ls -lh "$FONTS_DIR"
