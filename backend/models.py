from datetime import datetime
from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    entries = db.relationship('DiaryEntry', backref='author', lazy=True)


class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    sentiment_score = db.Column(db.Float, nullable=True)
    # Dominant emotion from NRCLex (joy, fear, anger, sadness, ...).
    emotion = db.Column(db.String(20), nullable=True)
    # User-supplied comma-separated tags, kept alongside the auto category
    # so the two labelling schemes can be compared.
    tags = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'category': self.category,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score,
            'emotion': self.emotion,
            'tags': self.tag_list,
            'timestamp': self.timestamp.isoformat(),
        }


class WeeklyInsight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insight_text = db.Column(db.Text, nullable=False)
    generated_on = db.Column(db.DateTime, default=lambda: datetime.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
