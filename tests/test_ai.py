from datetime import datetime
from types import SimpleNamespace

from backend import ai


def _entries():
    return [
        SimpleNamespace(
            timestamp=datetime(2026, 10, day),
            sentiment_score=0.2,
            category='Work',
            sentiment='Positive',
            text='I made progress on my work today.',
        )
        for day in (1, 2, 3)
    ]


def test_weekly_insight_retries_temporary_503(monkeypatch):
    class FakeModels:
        def __init__(self):
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise Exception('503 UNAVAILABLE: temporary high demand')
            return SimpleNamespace(text='A helpful reflection.')

    models = FakeModels()
    monkeypatch.setattr(ai.genai, 'Client', lambda api_key: SimpleNamespace(models=models))
    monkeypatch.setattr(ai.time, 'sleep', lambda seconds: None)

    result = ai.generate_weekly_insight(_entries(), 'test-key', 'test-model')

    assert result == 'A helpful reflection.'
    assert models.calls == 2


def test_weekly_insight_stops_after_three_503_attempts(monkeypatch):
    class FakeModels:
        def __init__(self):
            self.calls = 0

        def generate_content(self, **kwargs):
            self.calls += 1
            raise Exception('503 UNAVAILABLE: temporary high demand')

    models = FakeModels()
    monkeypatch.setattr(ai.genai, 'Client', lambda api_key: SimpleNamespace(models=models))
    monkeypatch.setattr(ai.time, 'sleep', lambda seconds: None)

    result = ai.generate_weekly_insight(_entries(), 'test-key', 'test-model')

    assert result == 'Gemini is temporarily busy. Please try again in a few minutes.'
    assert models.calls == 3
