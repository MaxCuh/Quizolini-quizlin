from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Quiz, Question, Answer

quiz = Blueprint('quiz', __name__)

@quiz.route('/dashboard')
@login_required
def dashboard():
    quizzes = Quiz.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', quizzes=quizzes)

@quiz.route('/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if request.method == 'POST':
        title = request.form.get('title')
        new_quiz = Quiz(title=title, user_id=current_user.id)
        db.session.add(new_quiz)
        db.session.commit()
        return redirect(url_for('quiz.dashboard'))
    return render_template('create_quiz.html')

@quiz.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def delete_quiz(quiz_id):
    q = Quiz.query.get_or_404(quiz_id)
    if q.user_id != current_user.id:
        flash('Ikke tilgang')
        return redirect(url_for('quiz.dashboard'))
    db.session.delete(q)
    db.session.commit()
    return redirect(url_for('quiz.dashboard'))
