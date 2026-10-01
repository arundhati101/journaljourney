"""Derived analytics that sit on top of the raw models: journaling streaks
and word-cloud image generation."""

import io
from datetime import timedelta
from collections import Counter

from .nlp import _stop_words


def current_streak(entries, today):
    """Longest run of consecutive calendar days ending today (or yesterday)
    on which the user wrote at least one entry.

    `entries` is any iterable of DiaryEntry. Returns an int number of days.
    """
    days = {e.timestamp.date() for e in entries}
    if not days:
        return 0

    # A streak is still "alive" if the user wrote today or yesterday.
    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def build_wordcloud_png(text):
    """Render `text` to a PNG (bytes) word cloud, or return None if either the
    wordcloud library is unavailable or there are no usable words."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        return None

    words = [w for w in text.lower().split() if w.isalpha() and w not in _stop_words]
    if not words:
        return None

    frequencies = Counter(words)
    cloud = WordCloud(
        width=900,
        height=450,
        background_color='white',
        colormap='OrRd',
        prefer_horizontal=0.9,
    ).generate_from_frequencies(frequencies)

    buffer = io.BytesIO()
    cloud.to_image().save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
