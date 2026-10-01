from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    send_file, abort,
)
from datetime import datetime
from .. import db
from ..models import DiaryEntry
from ..nlp import categorize_entry, analyze_sentiment, analyze_emotion
from ..services import current_streak, build_wordcloud_png

journal_bp = Blueprint('journal', __name__)


def _login_required():
    return 'user_id' in session


@journal_bp.route('/', methods=['GET', 'POST'])
def index():
    if not _login_required():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        text = request.form['diary_entry']
        tags = request.form.get('tags', '').strip() or None
        category = categorize_entry(text)
        sentiment, score = analyze_sentiment(text)
        emotion = analyze_emotion(text)

        db.session.add(DiaryEntry(
            text=text,
            category=category,
            sentiment=sentiment,
            sentiment_score=score,
            emotion=emotion,
            tags=tags,
            user_id=session['user_id'],
        ))
        db.session.commit()
        flash("Entry added successfully!", "success")
        return redirect(url_for('journal.entries'))

    all_entries = DiaryEntry.query.filter_by(user_id=session['user_id']).all()
    streak = current_streak(all_entries, datetime.now().date())
    return render_template('index.html', streak=streak)


@journal_bp.route('/entries')
def entries():
    if not _login_required():
        return redirect(url_for('auth.login'))

    search_query = request.args.get('search', '')
    q = DiaryEntry.query.filter_by(user_id=session['user_id']).order_by(DiaryEntry.timestamp.desc())
    if search_query:
        q = q.filter(DiaryEntry.text.contains(search_query))

    return render_template('entries.html', diary_entries=q.all(), search_query=search_query)


@journal_bp.route('/edit_entry/<int:index>', methods=['GET', 'POST'])
def edit_entry(index):
    if not _login_required():
        return redirect(url_for('auth.login'))

    entry = DiaryEntry.query.filter_by(id=index, user_id=session['user_id']).first()
    if not entry:
        flash("Entry not found.", "danger")
        return redirect(url_for('journal.entries'))

    if request.method == 'POST':
        text = request.form['diary_entry']
        entry.text = text
        entry.tags = request.form.get('tags', '').strip() or None
        # Re-run the NLP pipeline so labels stay consistent with edited text.
        entry.category = categorize_entry(text)
        entry.sentiment, entry.sentiment_score = analyze_sentiment(text)
        entry.emotion = analyze_emotion(text)
        db.session.commit()
        flash("Entry updated successfully!", "success")
        return redirect(url_for('journal.entries'))

    return render_template('edit.html', entry=entry)


@journal_bp.route('/delete_entry/<int:index>', methods=['POST'])
def delete_entry(index):
    if not _login_required():
        return redirect(url_for('auth.login'))

    entry = DiaryEntry.query.filter_by(id=index, user_id=session['user_id']).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash("Entry deleted successfully!", "success")
    else:
        flash("Entry not found.", "danger")

    return redirect(url_for('journal.entries'))


@journal_bp.route('/wordcloud')
def wordcloud_page():
    if not _login_required():
        return redirect(url_for('auth.login'))
    return render_template('wordcloud.html')


@journal_bp.route('/wordcloud.png')
def wordcloud_image():
    if not _login_required():
        return redirect(url_for('auth.login'))

    entries = DiaryEntry.query.filter_by(user_id=session['user_id']).all()
    combined = " ".join(e.text for e in entries)
    image = build_wordcloud_png(combined)
    if image is None:
        abort(404)
    return send_file(image, mimetype='image/png')
