from flask import Blueprint, jsonify, render_template, request, session
from services.stt_service import transcribe_audio
from services.llm_service import get_response
import os, tempfile

interview_bp = Blueprint('interview', __name__)
@interview_bp.route('/')
def interview_page():
    return render_template('interview.html')

@interview_bp.route('/health')
def health():
    return jsonify({'status': 'ok'})

@interview_bp.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    file = request.files['audio']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        result = transcribe_audio(tmp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

from services.llm_service import get_response

@interview_bp.route('/respond', methods=['POST'])
def respond():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text'}), 400
    history = session.get('interview_history', [])
    ai_text = get_response(data['text'], history)
    history.append({'role': 'user', 'content': data['text']})
    history.append({'role': 'assistant', 'content': ai_text})
    session['interview_history'] = history
    session.modified = True
    return jsonify({'response': ai_text, 'language': data.get('language', 'en')})

@interview_bp.route('/reset', methods=['POST'])
def reset():
    session.pop('interview_history', None)
    return jsonify({'status': 'reset'})

from services.avatar_service import create_avatar_video
# add this import at the top alongside the others

@interview_bp.route('/avatar', methods=['POST'])
def avatar():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text'}), 400
    try:
        video_url = create_avatar_video(data['text'])
        return jsonify({'video_url': video_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
