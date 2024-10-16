from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
import nltk
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import datetime

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('vader_lexicon')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# In-memory storage for diary entries and user credentials
diary_entries = []
users = {"testuser": "password"}  # Example user

category_keywords = {
    "Work": ["work", "job", "office", "project", "task", "meeting", "deadline", "client", "colleague", "manager",
             "report", "presentation", "progress", "achievement", "challenge", "success", "failure", "workload",
             "overtime", "promotion", "training", "evaluation", "assignment", "team", "supervisor", "email",
             "brainstorming", "conference", "agenda", "proposal", "feedback", "strategy", "break", "networking",
             "review", "schedule", "workshop", "coworker", "collaboration", "planning", "goals", "milestone",
             "briefing", "teleconference", "memo", "workflow", "performance", "resource", "target", "initiative",
             "motivation", "delegation", "leadership", "development", "productivity", "reporting"],
    "Health": ["health", "fitness", "exercise", "diet", "workout", "nutrition", "wellness", "gym", "running",
               "physical activity", "walking", "yoga", "meditation", "sleep", "hydration", "weight", "calories",
               "stress", "relaxation", "illness", "recovery", "therapy", "fatigue", "energy", "allergies",
               "mental health", "physical health", "self-care", "medication", "immune system", "vitamins",
               "supplements", "check-up", "doctor", "treatment", "balance", "strength", "endurance", "cardio",
               "mindfulness", "well-being", "prevention", "healing", "resilience", "rejuvenation", "detox", "hygiene",
               "rest"],
    "Relationships": ["love", "friend", "family", "partner", "relationship", "romance", "date", "marriage",
                      "engagement", "anniversary", "commitment", "trust", "support", "communication", "intimacy",
                      "conflict", "understanding", "compromise", "affection", "neighbors", "acquaintances", "pets",
                      "mentor", "roommate", "classmates", "children", "parents", "siblings", "spouse", "grandparents",
                      "relatives", "respect", "companionship", "loyalty", "patience", "empathy", "forgiveness",
                      "honesty", "shared values", "compatibility", "dedication", "bond", "connection", "harmony",
                      "friendship", "devotion", "caring", "togetherness", "faithfulness", "admiration", "nurturing",
                      "appreciation", "balance", "security", "dependability", "passion", "mutual goals",
                      "emotional support", "shared interests", "teamwork", "sacrifice", "growth",
                      "shared responsibilities"],
    "Personal Development": ["personal development", "growth", "self-improvement", "learning", "skills", "mindfulness",
                             "motivation", "goal-setting", "self-awareness", "discipline", "focus", "productivity",
                             "resilience", "confidence", "time management", "leadership", "creativity", "adaptability",
                             "emotional intelligence", "communication", "networking", "problem-solving",
                             "decision-making", "reflection", "positivity", "habits", "well-being", "health", "balance",
                             "purpose", "vision", "clarity", "self-care", "accountability", "ambition", "inspiration",
                             "growth mindset", "determination", "innovation", "flexibility", "persistence",
                             "work-life balance", "relationships", "gratitude", "assertiveness", "curiosity",
                             "optimism", "perspective", "meditation", "development", "goal", "learn", "improve",
                             "achieve", "self-discovery", "self-esteem", "self-reflection", "success mindset"],
    "Hobbies": ["hobby", "interest", "passion", "activity", "pastime", "enjoyment", "leisure", "creativity",
                "relaxation", "exploration", "pursuit", "craft", "art", "project", "skill", "recreation", "amusement",
                "expression", "fun", "enthusiasm", "creative outlet", "DIY", "gardening", "cooking", "baking",
                "painting", "love doing", "drawing", "photography", "writing", "reading", "music", "dancing", "singing",
                "acting", "knitting", "sewing", "sculpting", "woodworking", "pottery", "cycling", "hiking", "camping",
                "traveling", "collecting", "birdwatching", "astronomy", "gaming", "sports"]
}

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return tokens


def categorize_entry(diary_entry, category_keywords):
    preprocessed_entry = preprocess_text(diary_entry)
    category_counts = {category: 0 for category in category_keywords.keys()}
    for word in preprocessed_entry:
        for category, keywords in category_keywords.items():
            if word in keywords:
                category_counts[category] += 1
    max_category = max(category_counts, key=category_counts.get)
    return max_category


sid = SentimentIntensityAnalyzer()


def analyze_sentiment(diary_entry):
    sentiment_scores = sid.polarity_scores(diary_entry)
    if sentiment_scores['compound'] >= 0.05:
        sentiment = 'Positive'
    elif sentiment_scores['compound'] <= -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    return sentiment, sentiment_scores


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and users[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users:
            flash('Username already exists', 'danger')
        else:
            users[username] = password
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        diary_entry = request.form['diary_entry']
        category = categorize_entry(diary_entry, category_keywords)
        sentiment, sentiment_scores = analyze_sentiment(diary_entry)
        entry = {
            'text': diary_entry,
            'category': category,
            'sentiment': sentiment,
            'sentiment_scores': sentiment_scores,
            'username': session['username'],
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        diary_entries.append(entry)
        return redirect(url_for('entries'))

    return render_template('index.html')



@app.route('/entries')
def entries():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    user_entries = [entry for entry in diary_entries if entry['username'] == session['username']]

    if search_query:
        user_entries = [entry for entry in user_entries if search_query.lower() in entry['text'].lower()]

    return render_template('entries.html', diary_entries=user_entries, search_query=search_query)


@app.route('/delete_entry/<int:index>', methods=['POST'])
def delete_entry(index):
    if 'username' in session:
        user_entries = [entry for entry in diary_entries if entry['username'] == session['username']]
        if 0 <= index < len(user_entries):
            diary_entries.remove(user_entries[index])
            flash('Entry deleted successfully.', 'success')
        else:
            flash('Invalid entry index.', 'danger')
    else:
        flash('You need to be logged in to delete an entry.', 'danger')
    return redirect(url_for('entries'))


if __name__ == '__main__':
    app.run(debug=True)
