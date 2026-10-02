import nltk
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

def _ensure_nltk_data():
    """Download required NLTK corpora, but only the ones not already present.

    Guards each lookup so a machine that is offline (or behind a proxy that
    blocks the NLTK CDN) still starts as long as the data was fetched once.
    """
    required = {
        'punkt': 'tokenizers/punkt',
        'punkt_tab': 'tokenizers/punkt_tab',
        'stopwords': 'corpora/stopwords',
        'wordnet': 'corpora/wordnet',
        'vader_lexicon': 'sentiment/vader_lexicon',
    }
    for pkg, path in required.items():
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass


_ensure_nltk_data()

_stop_words = set(stopwords.words('english'))
_lemmatizer = WordNetLemmatizer()
_sid = SentimentIntensityAnalyzer()

CATEGORY_KEYWORDS = {
    "Work": [
        "work", "job", "office", "project", "task", "meeting", "deadline", "client", "manager", "team",
        "career", "business", "colleague", "coworker", "supervisor", "boss", "employee", "employer", "company", "workplace",
        "shift", "salary", "promotion", "interview", "presentation", "report", "email", "schedule", "budget", "strategy",
        "contract", "target", "assignment", "responsibility", "productivity", "leadership", "profession", "industry", "marketing", "sales",
        "finance", "accounting", "coding", "design", "engineering", "research", "analysis", "deployment", "customer", "vendor",
        "invoice", "desk", "commute", "conference", "negotiation", "recruitment", "hiring", "resignation", "overtime", "workload",
        "proposal", "deliverable", "department", "organization", "startup", "partnership", "promotion", "training", "presentation", "payroll",
    ],
    "Health": [
        "health", "fitness", "exercise", "gym", "diet", "sleep", "doctor", "meditation", "running", "walking",
        "nutrition", "wellness", "therapy", "hospital", "illness", "symptom", "recovery", "medication", "yoga", "stretching",
        "workout", "muscle", "cardio", "strength", "energy", "stress", "anxiety", "depression", "pain", "injury",
        "surgery", "dentist", "nurse", "patient", "appointment", "prescription", "vitamin", "protein", "hydration", "water",
        "routine", "rest", "relaxation", "breathing", "posture", "balance", "endurance", "weight", "heart", "meal",
        "checkup", "treatment", "diagnosis", "infection", "fever", "headache", "medicine", "healthy", "calorie", "cholesterol",
        "blood", "wellbeing", "mobility", "flexibility", "sickness", "clinic", "therapy", "mental", "physical", "recharge",
    ],
    "Relationships": [
        "love", "friend", "family", "partner", "relationship", "parents", "siblings", "marriage", "spouse", "child",
        "baby", "cousin", "relative", "friendship", "trust", "communication", "conflict", "support", "conversation", "date",
        "couple", "wedding", "breakup", "affection", "care", "bond", "connection", "argument", "apology", "forgiveness",
        "loyalty", "respect", "intimacy", "empathy", "kindness", "companionship", "loneliness", "reunion", "visit", "call",
        "message", "birthday", "anniversary", "dinner", "gathering", "celebration", "holiday", "parenting", "household", "inlaw",
        "aunt", "uncle", "niece", "nephew", "grandparent", "grandmother", "grandfather", "mother", "father", "daughter",
        "son", "brother", "sister", "boyfriend", "girlfriend", "roommate", "neighbor", "community", "social", "relative",
    ],
    "Personal Development": [
        "growth", "learning", "goal", "motivation", "discipline", "confidence", "improve", "skill", "habit", "practice",
        "progress", "challenge", "achievement", "success", "failure", "reflection", "mindfulness", "knowledge", "course", "study",
        "education", "training", "development", "focus", "patience", "courage", "resilience", "ambition", "purpose", "planning",
        "change", "decision", "creativity", "thinking", "problem", "awareness", "organization", "consistency", "effort", "perseverance",
        "adaptability", "independence", "responsibility", "certificate", "degree", "workshop", "mentor", "coaching", "feedback", "potential",
        "mindset", "selfcare", "selfesteem", "reflection", "determination", "curiosity", "communication", "confidence", "achievement", "success",
        "commitment", "initiative", "leadership", "time", "planning", "decisionmaking", "experimentation", "understanding", "mastery", "purposeful",
    ],
    "Hobbies": [
        "music", "reading", "writing", "gaming", "travel", "photography", "drawing", "cooking", "painting", "singing",
        "dancing", "hiking", "cycling", "gardening", "knitting", "crafts", "puzzle", "chess", "fishing", "swimming",
        "camping", "baking", "collecting", "film", "movie", "podcast", "instrument", "guitar", "piano", "sculpture",
        "pottery", "woodworking", "sewing", "origami", "astronomy", "stargazing", "birdwatching", "surfing", "skateboarding", "kayaking",
        "snorkeling", "bowling", "tennis", "badminton", "football", "basketball", "baseball", "soccer", "volleyball", "boardgame",
        "videogame", "animation", "blogging", "scrapbooking", "calligraphy", "modelmaking", "brewing", "tasting", "crochet", "embroidery",
        "jogging", "rowing", "sailing", "climbing", "diy", "decorating", "magic", "comedy", "theater", "acting",
    ],
}


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [w for w in tokens if w.isalnum() and w not in _stop_words]
    return [_lemmatizer.lemmatize(w) for w in tokens]


def categorize_entry(text):
    words = preprocess_text(text)
    scores = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for word in words:
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if word in keywords:
                scores[cat] += 1
    if max(scores.values()) == 0:
        return "Personal Development"
    return max(scores, key=scores.get)


def analyze_sentiment(text):
    compound = _sid.polarity_scores(text)['compound']
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return label, compound


def analyze_emotion(text):
    """Return the dominant NRC emotion for the text (e.g. joy, fear, anger).

    NRCLex maps words to Plutchik emotions via the NRC lexicon. We ignore the
    generic positive/negative valence buckets (VADER already covers those) and
    return the strongest specific emotion, or "neutral" when nothing fires.
    """
    try:
        from nrclex import NRCLex
    except ImportError:
        return "neutral"

    analyzer = NRCLex()
    analyzer.load_raw_text(text)
    scores = analyzer.affect_frequencies
    ignore = {'positive', 'negative'}
    emotions = {k: v for k, v in scores.items() if k not in ignore and v > 0}
    if not emotions:
        return "neutral"
    return max(emotions, key=emotions.get)


def score_text(text):
    return _sid.polarity_scores(text)['compound']
