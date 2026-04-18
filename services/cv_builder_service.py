import json
import re
from groq import Groq
import os

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return _client

CV_BUILD_PROMPT = """You are a professional CV writer for Malaysian job seekers.
Given structured input about a person's background, generate a polished, professional CV.

Return ONLY valid JSON with this exact structure:
{
  "name": "Full Name",
  "contact": "email | phone | city",
  "linkedin": "linkedin URL or empty string",
  "summary": "2-3 sentence professional summary tailored to their actual experience",
  "experience": [
    {
      "title": "Job Title or Role",
      "org": "Company, Place, or Context",
      "period": "Month Year – Month Year (or approximate)",
      "bullets": ["Strong action verb + specific achievement", "Second bullet point"]
    }
  ],
  "education": [
    {
      "degree": "Qualification or Degree",
      "institution": "School or University",
      "year": "Year",
      "notes": "Relevant grades or subjects if mentioned"
    }
  ],
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "activities": [
    {
      "title": "Role or Activity",
      "org": "Organisation or Context",
      "description": "One-line professional description"
    }
  ],
  "awards": ["Award name – brief description (Year)"]
}

Rules:
- Use strong action verbs: Managed, Coordinated, Achieved, Delivered, Supported, Developed
- Add plausible numbers where logical (e.g. "50+ customers daily", "team of 3")
- Do NOT invent anything not mentioned by the user
- If a section has no data, return an empty array []
- Write all content in professional CV language
- Summary should be honest and reflect the person's actual experience level
- Return ONLY the JSON object, nothing else, no markdown code blocks"""


def build_cv(data: dict) -> dict:
    lines = [
        f"Name: {data.get('name', '')}",
        f"Email: {data.get('email', '')}",
        f"Phone: {data.get('phone', '')}",
        f"City: {data.get('city', '')}",
        f"LinkedIn: {data.get('linkedin', '')}",
        "",
        "WORK / INFORMAL EXPERIENCE:",
    ]
    for i, exp in enumerate(data.get('experience', []), 1):
        lines.append(
            f"{i}. Title: {exp.get('title', '')} | "
            f"Organisation: {exp.get('org', '')} | "
            f"Period: {exp.get('period', '')}"
        )
        lines.append(f"   Description: {exp.get('description', '')}")

    lines.append("")
    lines.append("EDUCATION:")
    for i, edu in enumerate(data.get('education', []), 1):
        lines.append(
            f"{i}. Qualification: {edu.get('qualification', '')} | "
            f"Institution: {edu.get('institution', '')} | "
            f"Year: {edu.get('year', '')} | "
            f"Notes: {edu.get('notes', '')}"
        )

    lines.append("")
    lines.append(f"SKILLS: {data.get('skills', '')}")
    lines.append(f"ACTIVITIES & VOLUNTEERING: {data.get('activities', '')}")
    lines.append(f"AWARDS & ACHIEVEMENTS: {data.get('awards', '')}")

    user_content = "\n".join(lines)

    response = _get_client().chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=[
            {'role': 'system', 'content': CV_BUILD_PROMPT},
            {'role': 'user',   'content': user_content},
        ],
        max_tokens=2000,
        temperature=0.2,
    )
    text = response.choices[0].message.content.strip()
    # Strip markdown code fences if present
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        text = match.group(0)
    return json.loads(text)
