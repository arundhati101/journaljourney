from flask import Blueprint, render_template, redirect, url_for, session, flash
from .. import db, bcrypt
from ..models import User
from ..forms import LoginForm, SignupForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('journal.index'))

    form = SignupForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('auth.signup'))

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.add(User(username=form.username.data, password=hashed_pw))
        db.session.commit()
        flash("Account created successfully!", "success")
        return redirect(url_for('auth.login'))

    return render_template('signup.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('journal.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login Successful!", "success")
            return redirect(url_for('journal.index'))
        flash("Invalid Username or Password", "danger")

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('auth.login'))
