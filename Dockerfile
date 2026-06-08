FROM python:3.11-slim

# Install system dependencies: ffmpeg + guaranteed font packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set up font directory and copy system fonts as reliable fallbacks.
# Each font gets its own RUN step so a failure in one doesn't break others.
RUN mkdir -p bot/fonts bot/temp bot/logs

# Montserrat-Bold — try download first, fall back to DejaVu
RUN wget -q \
      "https://github.com/google/fonts/raw/main/ofl/montserrat/static/Montserrat-Bold.ttf" \
      -O bot/fonts/Montserrat-Bold.ttf 2>/dev/null \
    || cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf bot/fonts/Montserrat-Bold.ttf

# Arial — use Liberation Sans (metric-compatible free substitute)
RUN cp /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf bot/fonts/Arial.ttf \
    || cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf bot/fonts/Arial.ttf

# Roboto — try download first, fall back to DejaVu
RUN wget -q \
      "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf" \
      -O bot/fonts/Roboto-Regular.ttf 2>/dev/null \
    || cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf bot/fonts/Roboto-Regular.ttf

# Verify everything is ready
RUN echo "=== FFmpeg ===" && ffmpeg -version | head -1 \
    && echo "=== Fonts ===" && ls -lh bot/fonts/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "bot.main"]
