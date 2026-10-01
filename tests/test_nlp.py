"""Unit tests for the NLP pipeline and derived analytics."""

from datetime import date, timedelta
from types import SimpleNamespace

from backend.nlp import (
    preprocess_text, categorize_entry, analyze_sentiment, analyze_emotion, score_text,
)
from backend.services import current_streak


def test_preprocess_removes_stopwords_and_lemmatizes():
    tokens = preprocess_text("I am running to the meetings with my managers")
    assert 'the' not in tokens          # stopword removed
    assert 'i' not in tokens
    assert 'meeting' in tokens          # lemmatized from 'meetings'


def test_categorize_work():
    assert categorize_entry("I had a stressful meeting with my manager about the project") == "Work"


def test_categorize_health():
    assert categorize_entry("Went to the gym and focused on my fitness and diet today") == "Health"


def test_categorize_default_when_no_keywords():
    assert categorize_entry("The sky was a colour I could not name") == "Personal Development"


def test_sentiment_positive():
    label, score = analyze_sentiment("I am so happy and grateful, this was wonderful")
    assert label == "Positive"
    assert score > 0.05


def test_sentiment_negative():
    label, score = analyze_sentiment("I feel terrible, everything is awful and sad")
    assert label == "Negative"
    assert score < -0.05


def test_sentiment_neutral():
    label, _ = analyze_sentiment("The meeting is at three")
    assert label == "Neutral"


def test_score_text_matches_sentiment_score():
    text = "I am delighted with the results"
    assert score_text(text) == analyze_sentiment(text)[1]


def test_analyze_emotion_returns_string():
    emotion = analyze_emotion("I was terrified and full of fear during the storm")
    assert isinstance(emotion, str)
    assert emotion  # non-empty


def test_streak_counts_consecutive_days():
    today = date(2026, 7, 30)
    days = [today, today - timedelta(days=1), today - timedelta(days=2)]
    entries = [SimpleNamespace(timestamp=SimpleNamespace(date=lambda dd=dd: dd)) for dd in days]
    assert current_streak(entries, today) == 3


def test_streak_breaks_on_gap():
    today = date(2026, 7, 30)
    days = [today, today - timedelta(days=2)]  # missing yesterday
    entries = [SimpleNamespace(timestamp=SimpleNamespace(date=lambda dd=dd: dd)) for dd in days]
    assert current_streak(entries, today) == 1


def test_streak_zero_when_no_recent_entry():
    today = date(2026, 7, 30)
    days = [today - timedelta(days=5)]
    entries = [SimpleNamespace(timestamp=SimpleNamespace(date=lambda dd=dd: dd)) for dd in days]
    assert current_streak(entries, today) == 0


def test_streak_empty():
    assert current_streak([], date(2026, 7, 30)) == 0
