from flask_socketio import SocketIO, emit, join_room
from flask import request
from models import db, GameSession, Question, Answer, LeaderboardEntry
import time

socketio = SocketIO()
active_games = {}

@socketio.on('host_join')
def handle_host_join(data):
    session_id = data['session_id']
    join_room(f'game_{session_id}')
    if session_id not in active_games:
        active_games[session_id] = {
            'players': {},
            'current_question': 0,
            'started': False,
            'answers_received': {},
            'question_start_time': None
        }
    emit('host_joined', {'session_id': session_id})

@socketio.on('player_join')
def handle_player_join(data):
    session_id = data['session_id']
    nickname = data['nickname']
    join_room(f'game_{session_id}')
    if session_id not in active_games:
        emit('error', {'message': 'Spillet finnes ikke'})
        return
    active_games[session_id]['players'][request.sid] = {
        'nickname': nickname,
        'score': 0
    }
    emit('player_joined', {
        'nickname': nickname,
        'player_count': len(active_games[session_id]['players'])
    }, to=f'game_{session_id}')

@socketio.on('start_game')
def handle_start_game(data):
    session_id = data['session_id']
    game = active_games.get(session_id)
    if not game:
        return
    game['started'] = True
    send_question(session_id)

def send_question(session_id):
    game = active_games.get(session_id)
    if not game:
        return
    session = GameSession.query.get(session_id)
    questions = Question.query.filter_by(quiz_id=session.quiz_id).all()
    q_index = game['current_question']
    if q_index >= len(questions):
        end_game(session_id)
        return
    question = questions[q_index]
    game['answers_received'] = {}
    game['question_start_time'] = time.time()
    answers = [{'id': a.id, 'text': a.text} for a in question.answers]
    socketio.emit('new_question', {
        'question_index': q_index,
        'total_questions': len(questions),
        'question_text': question.text,
        'answers': answers,
        'time_limit': question.time_limit
    }, to=f'game_{session_id}')

@socketio.on('submit_answer')
def handle_answer(data):
    session_id = data['session_id']
    answer_id = data['answer_id']
    game = active_games.get(session_id)
    if not game or request.sid not in game['players']:
        return
    if request.sid in game['answers_received']:
        return
    answer = Answer.query.get(answer_id)
    is_correct = answer.is_correct if answer else False
    elapsed = time.time() - game['question_start_time']
    session = GameSession.query.get(session_id)
    questions = Question.query.filter_by(quiz_id=session.quiz_id).all()
    time_limit = questions[game['current_question']].time_limit
    if is_correct:
        points = max(100, int(1000 * (1 - elapsed / time_limit)))
        game['players'][request.sid]['score'] += points
    else:
        points = 0
    game['answers_received'][request.sid] = True
    emit('answer_result', {
        'correct': is_correct,
        'points': points,
        'total_score': game['players'][request.sid]['score']
    })
    if len(game['answers_received']) >= len(game['players']):
        show_leaderboard(session_id)

@socketio.on('next_question')
def handle_next_question(data):
    session_id = data['session_id']
    game = active_games.get(session_id)
    if game:
        game['current_question'] += 1
        send_question(session_id)

def show_leaderboard(session_id):
    game = active_games.get(session_id)
    if not game:
        return
    leaderboard = sorted(
        [{'nickname': p['nickname'], 'score': p['score']} for p in game['players'].values()],
        key=lambda x: x['score'], reverse=True
    )
    socketio.emit('show_leaderboard', {'leaderboard': leaderboard[:10]}, to=f'game_{session_id}')

def end_game(session_id):
    game = active_games.get(session_id)
    if not game:
        return
    for player in game['players'].values():
        entry = LeaderboardEntry(session_id=session_id, nickname=player['nickname'], score=player['score'])
        db.session.add(entry)
    session = GameSession.query.get(session_id)
    session.is_active = False
    db.session.commit()
    leaderboard = sorted(
        [{'nickname': p['nickname'], 'score': p['score']} for p in game['players'].values()],
        key=lambda x: x['score'], reverse=True
    )
    socketio.emit('game_over', {'leaderboard': leaderboard}, to=f'game_{session_id}')
    del active_games[session_id]

@socketio.on('disconnect')
def handle_disconnect():
    for session_id, game in list(active_games.items()):
        if request.sid in game['players']:
            nickname = game['players'][request.sid]['nickname']
            del game['players'][request.sid]
            socketio.emit('player_left', {
                'nickname': nickname,
                'player_count': len(game['players'])
            }, to=f'game_{session_id}')
            break