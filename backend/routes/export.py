import csv
import io
from flask import Blueprint, redirect, url_for, session, send_file, flash
from ..models import DiaryEntry

export_bp = Blueprint('export', __name__)


@export_bp.route('/export/csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    entries = (
        DiaryEntry.query
        .filter_by(user_id=session['user_id'])
        .order_by(DiaryEntry.timestamp.asc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Date', 'Category', 'Sentiment', 'Score', 'Emotion', 'Tags', 'Entry'])
    for e in entries:
        writer.writerow([
            e.timestamp.strftime('%Y-%m-%d %H:%M'),
            e.category,
            e.sentiment,
            f"{e.sentiment_score:.4f}" if e.sentiment_score is not None else '',
            e.emotion or '',
            e.tags or '',
            e.text.replace('\n', ' '),
        ])

    data = io.BytesIO(buffer.getvalue().encode('utf-8'))
    data.seek(0)
    return send_file(data, mimetype='text/csv', as_attachment=True,
                     download_name='journaljourney_entries.csv')


@export_bp.route('/export/pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except ImportError:
        flash("PDF export needs the 'reportlab' package. Install it and retry.", "danger")
        return redirect(url_for('journal.entries'))

    entries = (
        DiaryEntry.query
        .filter_by(user_id=session['user_id'])
        .order_by(DiaryEntry.timestamp.asc())
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    meta_style = ParagraphStyle('meta', parent=styles['Normal'],
                                fontSize=9, textColor='#888888')

    story = [Paragraph(f"JournalJourney — {session.get('username', '')}", styles['Title']),
             Spacer(1, 8)]

    for e in entries:
        meta = (f"{e.timestamp.strftime('%d %b %Y %I:%M %p')} · "
                f"{e.category} · {e.sentiment} · {e.emotion or 'n/a'}")
        story.append(Paragraph(meta, meta_style))
        story.append(Paragraph(e.text.replace('\n', '<br/>'), styles['BodyText']))
        story.append(Spacer(1, 12))

    if not entries:
        story.append(Paragraph("No entries yet.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                     download_name='journaljourney_entries.pdf')
