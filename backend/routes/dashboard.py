from flask import Blueprint, render_template, redirect, url_for, session
from datetime import datetime, timedelta
from collections import Counter
from ..models import DiaryEntry
from ..services import current_streak

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    today = datetime.now().date()
    window_start = today - timedelta(days=29)

    entries = (
        DiaryEntry.query
        .filter_by(user_id=session['user_id'])
        .filter(DiaryEntry.timestamp >= datetime.combine(window_start, datetime.min.time()))
        .order_by(DiaryEntry.timestamp.asc())
        .all()
    )

    all_entries = DiaryEntry.query.filter_by(user_id=session['user_id']).all()
    streak = current_streak(all_entries, today)
    emotion_counts = Counter(e.emotion for e in entries if e.emotion)

    day_data = {}
    for entry in entries:
        day = entry.timestamp.date()
        bucket = day_data.setdefault(day, {'scores': [], 'cats': Counter(), 'count': 0})
        bucket['count'] += 1
        if entry.category:
            bucket['cats'][entry.category] += 1
        if entry.sentiment_score is not None:
            bucket['scores'].append(entry.sentiment_score)

    def build_dataset(num_days, label_fmt):
        start = today - timedelta(days=num_days - 1)
        day_list = [start + timedelta(days=i) for i in range(num_days)]
        dates = [d.strftime(label_fmt) for d in day_list]

        daily_scores = []
        for d in day_list:
            scores = day_data.get(d, {}).get('scores')
            daily_scores.append(round(sum(scores) / len(scores), 4) if scores else None)

        rolling_avg = []
        for i in range(len(daily_scores)):
            if i + 1 < 7:
                rolling_avg.append(None)
                continue
            window_slice = [s for s in daily_scores[i - 6:i + 1] if s is not None]
            rolling_avg.append(round(sum(window_slice) / len(window_slice), 4) if window_slice else None)

        window_scores, cat_counter, total_entries = [], Counter(), 0
        for d in day_list:
            bucket = day_data.get(d)
            if not bucket:
                continue
            total_entries += bucket['count']
            window_scores.extend(bucket['scores'])
            cat_counter.update(bucket['cats'])

        return {
            'dates': dates,
            'daily_scores': daily_scores,
            'rolling_avg': rolling_avg,
            'total_entries': total_entries,
            'avg_sentiment': round(sum(window_scores) / len(window_scores), 4) if window_scores else 0.0,
            'most_common_category': cat_counter.most_common(1)[0][0] if cat_counter else "N/A",
        }

    return render_template('dashboard.html',
                           data_7=build_dataset(7, '%a %d'),
                           data_30=build_dataset(30, '%b %d'),
                           streak=streak,
                           emotion_counts=dict(emotion_counts))
