#!/bin/bash
# Download all watermark bot fonts from Google Fonts CDN.
# Run once during Docker build or Railway startup.

set -e

FONTS_DIR="${FONTS_DIR:-bot/fonts}"
mkdir -p "$FONTS_DIR"

echo "Downloading fonts to $FONTS_DIR ..."

BASE="https://github.com/google/fonts/raw/main"

download() {
    local url="$1"
    local dest="$FONTS_DIR/$2"
    if [ ! -f "$dest" ]; then
        echo "  → $2"
        curl -fsSL "$url" -o "$dest" || wget -q "$url" -O "$dest"
    else
        echo "  ✓ $2 (already exists)"
    fi
}

# ── Montserrat Bold ──────────────────────────────────────────────────────────
download \
  "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf" \
  "Montserrat-Bold.ttf"

# ── Roboto Bold ──────────────────────────────────────────────────────────────
download \
  "$BASE/ofl/roboto/Roboto-Bold.ttf" \
  "Roboto-Bold.ttf"

# ── Open Sans Bold ───────────────────────────────────────────────────────────
download \
  "https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf" \
  "OpenSans-Bold.ttf"

# ── Oswald Bold ──────────────────────────────────────────────────────────────
download \
  "$BASE/ofl/oswald/Oswald-Bold.ttf" \
  "Oswald-Bold.ttf"

# ── Bebas Neue ───────────────────────────────────────────────────────────────
download \
  "$BASE/ofl/bebasneue/BebasNeue-Regular.ttf" \
  "BebasNeue-Regular.ttf"

# ── Raleway Bold ─────────────────────────────────────────────────────────────
download \
  "$BASE/ofl/raleway/Raleway-Bold.ttf" \
  "Raleway-Bold.ttf"

# ── Playfair Display Bold ────────────────────────────────────────────────────
download \
  "$BASE/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf" \
  "PlayfairDisplay-Bold.ttf"

# ── Lato Bold ────────────────────────────────────────────────────────────────
download \
  "$BASE/ofl/lato/Lato-Bold.ttf" \
  "Lato-Bold.ttf"

# ── Ubuntu Bold ──────────────────────────────────────────────────────────────
download \
  "$BASE/ufl/ubuntu/Ubuntu-Bold.ttf" \
  "Ubuntu-Bold.ttf"

# ── Roboto Condensed Bold ────────────────────────────────────────────────────
download \
  "$BASE/ofl/robotocondensed/RobotoCondensed-Bold.ttf" \
  "RobotoCondensed-Bold.ttf"

# ── Arial (system fallback — copy if present) ────────────────────────────────
ARIAL_SRC="/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"
if [ -f "$ARIAL_SRC" ] && [ ! -f "$FONTS_DIR/Arial.ttf" ]; then
    cp "$ARIAL_SRC" "$FONTS_DIR/Arial.ttf"
    echo "  → Arial.ttf (from system)"
fi

echo "Done. Fonts in $FONTS_DIR:"
ls -lh "$FONTS_DIR"
