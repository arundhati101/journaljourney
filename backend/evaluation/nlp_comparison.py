"""Sentiment-model comparison: VADER vs TextBlob.

An evaluation harness for the project report. It runs both models over a small
hand-labelled set of journal-style sentences and prints per-model accuracy plus
a confusion-style breakdown. This is the evidence behind the design decision to
use VADER (which is tuned for short, informal, social-media-like text) as the
primary sentiment engine.

Run:  python -m backend.evaluation.nlp_comparison
"""

from nltk.sentiment import SentimentIntensityAnalyzer

# Hand-labelled evaluation set (text, gold_label). Extend this with real,
# anonymised entries to strengthen the reported numbers.
LABELLED = [
    ("I had the best day ever, everything went perfectly", "Positive"),
    ("I'm so grateful for my friends and family", "Positive"),
    ("Finally finished my project and I feel accomplished", "Positive"),
    ("What a wonderful, relaxing weekend", "Positive"),
    ("I aced my exam and I'm thrilled", "Positive"),
    ("Everything is falling apart and I feel hopeless", "Negative"),
    ("I'm exhausted, stressed, and close to burnout", "Negative"),
    ("That was a terrible, disappointing meeting", "Negative"),
    ("I feel so lonely and sad tonight", "Negative"),
    ("I'm anxious about the deadline and can't sleep", "Negative"),
    ("I went to the store and bought some milk", "Neutral"),
    ("The meeting is scheduled for 3pm tomorrow", "Neutral"),
    ("I read a chapter of my book before bed", "Neutral"),
    ("Today was an ordinary day at the office", "Neutral"),
    ("I walked to work and then came home", "Neutral"),
]

_sid = SentimentIntensityAnalyzer()


def vader_label(text):
    compound = _sid.polarity_scores(text)['compound']
    if compound >= 0.05:
        return "Positive"
    if compound <= -0.05:
        return "Negative"
    return "Neutral"


def textblob_label(text):
    from textblob import TextBlob
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.05:
        return "Positive"
    if polarity < -0.05:
        return "Negative"
    return "Neutral"


def evaluate(model_fn, name):
    correct = 0
    per_class = {}
    for text, gold in LABELLED:
        pred = model_fn(text)
        bucket = per_class.setdefault(gold, {'correct': 0, 'total': 0})
        bucket['total'] += 1
        if pred == gold:
            correct += 1
            bucket['correct'] += 1
    accuracy = correct / len(LABELLED)

    print(f"\n=== {name} ===")
    print(f"Overall accuracy: {accuracy:.1%}  ({correct}/{len(LABELLED)})")
    for label, b in sorted(per_class.items()):
        print(f"  {label:<9} {b['correct']}/{b['total']}")
    return accuracy


def main():
    print("Sentiment model comparison on a hand-labelled journal set")
    print("=" * 58)
    vader_acc = evaluate(vader_label, "VADER (NLTK)")
    try:
        tb_acc = evaluate(textblob_label, "TextBlob")
    except ImportError:
        print("\nTextBlob not installed — skipping (pip install textblob).")
        return

    print("\n" + "=" * 58)
    winner = "VADER" if vader_acc >= tb_acc else "TextBlob"
    print(f"Conclusion: {winner} performs better on this set. "
          f"VADER is chosen for production because it is rule-based, "
          f"needs no training data, and is tuned for short informal text.")


if __name__ == '__main__':
    main()
