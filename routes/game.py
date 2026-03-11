from flask import Blueprint
game = Blueprint('game', __name__)
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Quiz, GameSession

game = Blueprint('game', __name__)

@game.route('/lobby/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def lobby(quiz_id):
    q = Quiz.query.get_or_404(quiz_id)
    session = GameSession(
        quiz_id=quiz_id,
        pin=GameSession.generate_pin()
    )
    db.session.add(session)
    db.session.commit()
    return render_template('lobby.html', quiz=q, session=session)

@game.route('/game/<int:session_id>')
def game_view(session_id):
    session = GameSession.query.get_or_404(session_id)
    quiz = Quiz.query.get_or_404(session.quiz_id)
    return render_template('game.html', session=session, quiz=quiz)

@game.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        pin = request.form.get('pin')
        session = GameSession.query.filter_by(pin=pin, is_active=True).first()
        if session:
            return redirect(url_for('game.game_view', session_id=session.id))
        flash('Fant ingen aktiv quiz med den PIN-koden')
    return redirect(url_for('auth.login'))
