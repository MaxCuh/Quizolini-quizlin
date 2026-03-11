from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    return redirect(url_for('quiz.dashboard'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input') 
        password = request.form.get('password')

        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('quiz.dashboard'))

        flash('Feil brukernavn/epost eller passord', 'error')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passordene stemmer ikke', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Brukernavnet er allerede tatt', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Eposten er allerede registrert', 'error')
            return render_template('register.html')

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('quiz.dashboard'))

    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Admin-side (fra wombokombo)
@auth.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return 'Ingen tilgang', 403
    users = User.query.all()
    return render_template('admin.html', users=users)