from flask import Blueprint, render_template, redirect, url_for, session, current_app
from datetime import datetime, timedelta
from .. import db
from ..models import DiaryEntry, WeeklyInsight
from ..ai import generate_weekly_insight, INSUFFICIENT_ENTRIES_MSG

insights_bp = Blueprint('insights', __name__)


@insights_bp.route('/insights')
def insights():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cutoff = datetime.now() - timedelta(days=7)

    cached = (
        WeeklyInsight.query
        .filter_by(user_id=user_id)
        .filter(WeeklyInsight.generated_on >= cutoff)
        .order_by(WeeklyInsight.generated_on.desc())
        .first()
    )
    if cached:
        return render_template('insights.html',
                               insight_text=cached.insight_text,
                               generated_on=cached.generated_on)

    entries = (
        DiaryEntry.query
        .filter_by(user_id=user_id)
        .order_by(DiaryEntry.timestamp.desc())
        .limit(7)
        .all()
    )

    api_key = current_app.config['GEMINI_API_KEY']
    model = current_app.config['GEMINI_MODEL']
    insight_text = generate_weekly_insight(entries, api_key, model)

    if insight_text == INSUFFICIENT_ENTRIES_MSG:
        return render_template('insights.html', insight_text=insight_text, generated_on=None)

    insight = WeeklyInsight(insight_text=insight_text, user_id=user_id)
    db.session.add(insight)
    db.session.commit()

    return render_template('insights.html',
                           insight_text=insight.insight_text,
                           generated_on=insight.generated_on)


@insights_bp.route('/insights/refresh', methods=['POST'])
def insights_refresh():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    WeeklyInsight.query.filter_by(user_id=session['user_id']).delete()
    db.session.commit()
    return redirect(url_for('insights.insights'))
