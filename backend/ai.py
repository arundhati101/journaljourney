import google.genai as genai
import time

INSUFFICIENT_ENTRIES_MSG = "Write at least 3 entries this week to unlock your AI insight."


def generate_weekly_insight(entries, api_key, model):
    if len(entries) < 3:
        return INSUFFICIENT_ENTRIES_MSG

    if not api_key:
        return (
            "AI insights are unavailable: the GEMINI_API_KEY is not "
            "configured. Add it to your .env file to enable this feature."
        )

    entry_lines = []
    for entry in entries:
        date_str = entry.timestamp.strftime('%Y-%m-%d')
        score_str = f"{entry.sentiment_score:.2f}" if entry.sentiment_score is not None else "N/A"
        snippet = entry.text[:300].replace("\n", " ").strip()
        entry_lines.append(
            f"- Date: {date_str} | Category: {entry.category} | "
            f"Sentiment: {entry.sentiment} (score {score_str})\n"
            f"  Entry: {snippet}"
        )

    prompt = (
        "You are a compassionate journaling coach. Based on the following "
        "journal entries from the past week, provide a personal insight in "
        "exactly 3 short paragraphs:\n\n"
        "Paragraph 1 — Emotional pattern: Describe the emotional arc or "
        "dominant mood across the week.\n"
        "Paragraph 2 — Recurring themes: Identify 2-3 topics or situations "
        "that appear repeatedly.\n"
        "Paragraph 3 — Actionable suggestion: Give one specific, practical "
        "suggestion the person can act on this week.\n\n"
        "Keep the tone warm, non-judgmental, and personal. Do not use bullet "
        "points. Do not use headings. Write as if you are speaking directly "
        "to the person.\n\n"
        "Journal entries:\n"
        + "\n".join(entry_lines)
    )

    client = genai.Client(api_key=api_key)
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text.strip()
        except Exception as error:
            is_temporary_overload = (
                getattr(error, 'code', None) == 503
                or '503 UNAVAILABLE' in str(error)
                or ('503' in str(error) and 'UNAVAILABLE' in str(error))
            )
            if is_temporary_overload and attempt < 2:
                time.sleep(attempt + 1)
                continue
            if is_temporary_overload:
                return "Gemini is temporarily busy. Please try again in a few minutes."
            return f"Could not generate your insight right now. Please try again later. ({error})"
