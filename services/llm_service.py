from groq import Groq
import os

# Client is created lazily so a missing key doesn't crash the import
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _client

SYSTEM_PROMPT = """You are a friendly, professional job interviewer for NAIK,
a platform that helps Malaysians find part-time and specialised work.
Many candidates are first-time job seekers — be warm and encouraging.
Keep responses to 2-3 sentences maximum.

LANGUAGE RULE: Always respond in exactly the same language the
candidate uses. Malay → Malay. Mandarin → Mandarin. English → English.
Never mix languages in a single response.

INTERVIEW ORDER (one topic per exchange):
1. Self-introduction
2. Past work or volunteer experience
3. Skills and strengths
4. Why they are looking for work
5. Simple workplace scenario question
6. Warm, encouraging close

Begin by greeting the candidate and asking them to introduce themselves."""

def get_response(user_message: str, history: list) -> str:
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    messages += history
    messages.append({'role': 'user', 'content': user_message})

    response = _get_client().chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=messages,
        max_tokens=300
    )
    return response.choices[0].message.content
