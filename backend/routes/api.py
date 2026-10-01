"""JSON REST API.

A thin machine-readable layer over the same models the HTML views use, so the
app could later be driven by a separate SPA or mobile client. Authentication
reuses the session cookie; a 401 is returned for unauthenticated requests
instead of an HTML redirect.
"""

from functools import wraps
from datetime import datetime
from flask import Blueprint, jsonify, request, session
from .. import db
from ..models import DiaryEntry
from ..nlp import categorize_entry, analyze_sentiment, analyze_emotion
from ..services import current_streak

api_bp = Blueprint('api', __name__, url_prefix='/api')


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify(error='Authentication required'), 401
        return view(*args, **kwargs)
    return wrapped


@api_bp.route('/entries', methods=['GET'])
@api_login_required
def list_entries():
    entries = (
        DiaryEntry.query
        .filter_by(user_id=session['user_id'])
        .order_by(DiaryEntry.timestamp.desc())
        .all()
    )
    return jsonify(entries=[e.to_dict() for e in entries])


@api_bp.route('/entries', methods=['POST'])
@api_login_required
def create_entry():
    payload = request.get_json(silent=True) or {}
    text = (payload.get('text') or '').strip()
    if not text:
        return jsonify(error="'text' is required"), 400

    sentiment, score = analyze_sentiment(text)
    entry = DiaryEntry(
        text=text,
        category=categorize_entry(text),
        sentiment=sentiment,
        sentiment_score=score,
        emotion=analyze_emotion(text),
        tags=(payload.get('tags') or None),
        user_id=session['user_id'],
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry=entry.to_dict()), 201


@api_bp.route('/entries/<int:entry_id>', methods=['GET'])
@api_login_required
def get_entry(entry_id):
    entry = DiaryEntry.query.filter_by(id=entry_id, user_id=session['user_id']).first()
    if not entry:
        return jsonify(error='Not found'), 404
    return jsonify(entry=entry.to_dict())


@api_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@api_login_required
def delete_entry(entry_id):
    entry = DiaryEntry.query.filter_by(id=entry_id, user_id=session['user_id']).first()
    if not entry:
        return jsonify(error='Not found'), 404
    db.session.delete(entry)
    db.session.commit()
    return jsonify(deleted=entry_id)


@api_bp.route('/stats', methods=['GET'])
@api_login_required
def stats():
    entries = DiaryEntry.query.filter_by(user_id=session['user_id']).all()
    scores = [e.sentiment_score for e in entries if e.sentiment_score is not None]
    from collections import Counter
    categories = Counter(e.category for e in entries)
    emotions = Counter(e.emotion for e in entries if e.emotion)
    return jsonify(
        total_entries=len(entries),
        average_sentiment=round(sum(scores) / len(scores), 4) if scores else 0.0,
        streak=current_streak(entries, datetime.now().date()),
        categories=dict(categories),
        emotions=dict(emotions),
    )
