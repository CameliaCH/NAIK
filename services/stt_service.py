from groq import Groq
import os

# Client is created lazily so a missing key doesn't crash the import
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _client

LANGUAGE_MAP = {
    'english': 'en',
    'malay':   'ms',
    'chinese': 'zh',
    'mandarin':'zh',
}

def transcribe_audio(file_path: str) -> dict:
    with open(file_path, 'rb') as f:
        response = _get_client().audio.transcriptions.create(
            model='whisper-large-v3',
            file=f,
            response_format='verbose_json'
        )
    raw = (response.language or 'english').lower()
    return {
        'text':         response.text,
        'language':     LANGUAGE_MAP.get(raw, 'en'),
        'raw_language': raw
    }
