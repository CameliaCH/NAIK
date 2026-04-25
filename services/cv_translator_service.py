from groq import Groq
import os

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _client

SYSTEM_PROMPT = """You are a professional CV writer helping Malaysians
rewrite their everyday experience into polished CV language.

Rules:
- Keep it to 1-2 sentences maximum
- Use strong action verbs (Managed, Assisted, Coordinated, Achieved, Operated)
- Add realistic numbers where logical (e.g. "50+ customers daily")
- Do NOT invent qualifications or jobs that were not mentioned
- Respond ONLY with the rewritten CV line — no explanation, no preamble
- Match the language the user writes in (Malay → Malay, English → English)"""

CAREGIVING_PROMPT = """You are a professional CV writer specialising in helping Malaysian women re-enter the workforce after a caregiving break.

Your job is to reframe caregiving, home management, and family responsibilities as professional, transferable skills for a CV.

Rules:
- Translate the caregiving experience into 1-3 strong CV bullet points
- Use professional action verbs: Managed, Coordinated, Budgeted, Organised, Supervised, Negotiated, Planned, Advocated
- Map caregiving to real workplace skills: budget management, scheduling, health coordination, child development support, household project management
- NEVER mention children, spouse, or family by name — write as professional skills
- Add realistic context where it fits (e.g. "Managed household budget of RM X,000/month")
- Do NOT invent qualifications that were not implied
- Respond ONLY with the CV bullet points — no explanation, no preamble
- Match the language the user writes in (Malay → Malay, English → English)"""

def translate_to_cv(raw_experience: str) -> str:
    response = _get_client().chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': raw_experience}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def translate_caregiving_to_cv(raw_experience: str) -> str:
    response = _get_client().chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': CAREGIVING_PROMPT},
            {'role': 'user',   'content': raw_experience}
        ],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()