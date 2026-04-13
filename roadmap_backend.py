"""
roadmap_backend.py  (v2 — Supabase-only, no AI)
────────────────────────────────────────────────
Replaces the Gemini AI call with a smart Supabase query.

HOW IT WORKS:
  1. Receives the user profile from the frontend (interest, age, education, skills, income_mode, location, lang)
  2. Queries the Supabase `jobs` table for jobs matching the user's interest category
  3. Applies eligibility filters: min_age, education_min, cert_required
  4. Scores & ranks remaining jobs by how well they match the user's skills and income_mode
  5. Returns the top 3 as career paths, personalised with the user's name/location/skills

SETUP:
  pip install flask requests python-dotenv
  Set in .env:
    SUPABASE_URL=https://yourproject.supabase.co
    SUPABASE_ANON_KEY=eyJ...
"""

import os
import re
from flask import Blueprint, request, jsonify, current_app

roadmap_bp = Blueprint('roadmap', __name__)

# Education level ordering (higher index = more education)
EDUCATION_ORDER = ['primary', 'secondary_incomplete', 'spm_incomplete', 'spm']

# Skill value mappings — skills that align with which job categories
SKILL_CATEGORY_AFFINITY = {
    'manual_labor':     ['trades', 'logistics', 'food'],
    'cooking':          ['food'],
    'driving':          ['logistics', 'trades'],
    'computer_basic':   ['tech', 'biz', 'creative'],
    'social_media':     ['creative', 'biz'],
    'sales':            ['biz', 'creative'],
    'customer_service': ['biz', 'care', 'food'],
    'caregiving':       ['care'],
}


# ── HELPERS ────────────────────────────────────────────────────
def _supabase_headers():
    key = os.environ.get('SUPABASE_KEY', '')
    return {
        'apikey':        key,
        'Authorization': f'Bearer {key}',
        'Content-Type':  'application/json',
    }


def _education_ok(job_edu_min: str, user_edu: str) -> bool:
    """Return True if user meets or exceeds the job's education requirement."""
    try:
        return EDUCATION_ORDER.index(user_edu) >= EDUCATION_ORDER.index(job_edu_min)
    except ValueError:
        return True   # unknown value → don't filter out


def _age_ok(job_min_age: int, user_age_range: str) -> bool:
    """Return True if the user's age range satisfies the job's minimum age."""
    range_min = {
        '15-17': 15,
        '18-22': 18,
        '23-29': 23,
        '30+':   30,
    }.get(user_age_range, 18)
    return range_min >= job_min_age


def _score_job(job: dict, profile: dict) -> int:
    """
    Score a job's relevance to this user (higher = better match).
    Scoring factors:
      +3  each user skill that matches the job category's skill affinities
      +2  income_mode matches (immediate → entry salary high; upskill → growth potential)
      +1  not physically demanding (for non-manual workers)
      +1  no internet required (for users without computer skills)
    """
    score = 0
    user_skills   = profile.get('skills', [])
    user_category = profile.get('interest', 'biz')
    income_mode   = profile.get('income_mode', 'immediate')

    # Skill affinity boost
    for skill in user_skills:
        if user_category in SKILL_CATEGORY_AFFINITY.get(skill, []):
            score += 3

    # Income mode fit
    if income_mode == 'immediate':
        # Prefer higher entry salary
        score += max(0, (job.get('entry_salary_min', 1400) - 1400) // 100)
    else:
        # Prefer higher target salary (growth potential)
        score += max(0, (job.get('target_salary_max', 3000) - 3000) // 200)

    # Physical demands
    if not job.get('physically_demanding') and 'manual_labor' not in user_skills:
        score += 1

    # Internet requirement
    if not job.get('internet_required') and 'computer_basic' not in user_skills:
        score += 1

    return score


def _fill_placeholders(text: str, name: str, age: str, location: str, skills_str: str) -> str:
    """Replace {name}, {age}, {location}, {skills} in template strings."""
    if not isinstance(text, str):
        return text
    return (text
            .replace('{name}',     name)
            .replace('{age}',      age)
            .replace('{location}', location)
            .replace('{skills}',   skills_str))


def _personalise(obj, name, age, location, skills_str):
    """Recursively replace placeholders in strings inside a dict/list."""
    if isinstance(obj, str):
        return _fill_placeholders(obj, name, age, location, skills_str)
    if isinstance(obj, list):
        return [_personalise(i, name, age, location, skills_str) for i in obj]
    if isinstance(obj, dict):
        return {k: _personalise(v, name, age, location, skills_str) for k, v in obj.items()}
    return obj


def _build_income_ladder(job: dict, lang: str) -> list:
    """Convert the job's income_ladder JSONB rows into the JS-expected format."""
    ladder = job.get('income_ladder', [])
    result = []
    for row in ladder:
        result.append({
            'stage':  row.get(f'stage_{lang}', row.get('stage_en', '')),
            'role':   row.get(f'role_{lang}',  row.get('role_en', '')),
            'income': row.get('income', ''),
            'current': row.get('current', False),
            'tip':    row.get(f'tip_{lang}',   row.get('tip_en', '')),
        })
    return result


def _build_phase(phase_data: dict, lang: str, phase_num: int, courses_override=None) -> dict:
    """Convert a phase JSONB object into the shape the JS renderer expects."""
    if not phase_data:
        return {}

    tasks = []
    for tk in phase_data.get('tasks', []):
        tasks.append({
            'title':  tk.get(f'title_{lang}', tk.get('title_en', '')),
            'detail': tk.get(f'detail_{lang}', tk.get('detail_en', '')),
        })

    phase = {
        'num':          phase_num,
        'title':        phase_data.get(f'title_{lang}', phase_data.get('title_en', '')),
        'duration':     phase_data.get(f'duration_{lang}', phase_data.get('duration_en', '')),
        'colorClass':   f'p{phase_num}',
        'isApplyPhase': phase_num == 1,
        'tasks':        tasks,
        'tip':          phase_data.get(f'tip_{lang}', phase_data.get('tip_en', '')),
    }

    # Phase 1: add immediateJobKeywords
    if phase_num == 1:
        phase['immediateJobKeywords'] = phase_data.get('immediate_job_keywords', [])

    # Phase 2: add courses array
    if phase_num == 2:
        raw_courses = courses_override or phase_data.get('courses', [])
        phase['courses'] = [
            {
                'name':     c.get('name', ''),
                'provider': c.get('provider', ''),
                'url':      c.get('url', ''),
                'duration': c.get(f'duration_{lang}', c.get('duration_en', '')),
                'free':     c.get('free', True),
            }
            for c in raw_courses
        ]

    # Phase 3: add single course object
    if phase_num == 3:
        c = phase_data.get('course', {})
        if c:
            phase['course'] = {
                'name':     c.get('name', ''),
                'provider': c.get('provider', ''),
                'url':      c.get('url', ''),
                'duration': c.get(f'duration_{lang}', c.get('duration_en', '')),
                'free':     c.get('free', True),
            }

    return phase


def _job_to_career_path(job: dict, idx: int, profile: dict, lang: str) -> dict:
    """Convert a `jobs` DB row into the careerPath shape the JS frontend expects."""
    option_ids    = ['A', 'B', 'C']
    name          = profile.get('name', 'You' if lang == 'en' else 'Anda')
    age           = profile.get('age', '')
    location      = profile.get('location', 'Malaysia')
    skills_list   = (profile.get('skills') or [])
    skills_str    = ', '.join(skills_list) if skills_list else ('your current skills' if lang == 'en' else 'kemahiran anda')

    # Core fields
    path = {
        'id':           option_ids[idx] if idx < 3 else str(idx + 1),
        'emoji':        job.get('emoji', '💼'),
        'title':        f"{job.get('emoji','💼')} Option {option_ids[idx] if idx<3 else idx+1}: {job.get(f'title_{lang}', job.get('title_en',''))}",
        'targetJob':    job.get(f'target_job_{lang}',   job.get('target_job_en', '')),
        'targetSalary': f"RM{job.get('target_salary_min',2500):,}–{job.get('target_salary_max',4000):,}/{'month' if lang=='en' else 'bulan'}",
        'entryJob':     job.get(f'entry_job_{lang}',    job.get('entry_job_en', '')),
        'entrySalary':  f"RM{job.get('entry_salary_min',1400):,}–{job.get('entry_salary_max',1800):,}/{'month' if lang=='en' else 'bulan'}",
        'timeline':     f"{job.get('timeline_years','2–3')} {'years' if lang=='en' else 'tahun'}",
        'tagline':      job.get(f'tagline_{lang}',       job.get('tagline_en', '')),
        'jobDesc':      job.get(f'job_desc_{lang}',      job.get('job_desc_en', '')),
        'safetyRating': job.get(f'safety_rating_{lang}', job.get('safety_rating_en', 'Steady Growth')),
        'incomeType':   job.get('income_type', 'fixed'),
        'certRequired': job.get('cert_required', False),
        'certName':     job.get('cert_name', ''),
        'physicallyDemanding': job.get('physically_demanding', False),
        'internetRequired':    job.get('internet_required', False),
        'growthPaths':  job.get(f'growth_paths_{lang}', job.get('growth_paths_en', [])),
        'skillsToBuild': job.get(f'skills_to_build_{lang}', job.get('skills_to_build_en', [])),
        'helpfulExperience': job.get(f'helpful_experience_{lang}', job.get('helpful_experience_en', [])),
        'jobSearchKeywords': job.get('jobstreet_keywords', []),
    }

    # whyFit — personalise template
    why_raw  = job.get(f'why_fit_{lang}', job.get('why_fit_en', ''))
    why_tags = job.get(f'why_fit_tags_{lang}', job.get('why_fit_tags_en', []))
    path['whyFit']     = _fill_placeholders(why_raw, name, age, location, skills_str)
    path['whyFitTags'] = why_tags

    # Motivation
    motiv = job.get(f'motivation_{lang}', job.get('motivation_en', ''))
    path['motivation'] = _fill_placeholders(motiv, name, age, location, skills_str)

    # Income ladder
    path['incomeLadder'] = _build_income_ladder(job, lang)

    # 3 Phases
    path['phases'] = [
        _build_phase(job.get('phase1', {}), lang, 1),
        _build_phase(job.get('phase2', {}), lang, 2, courses_override=job.get('courses', [])),
        _build_phase(job.get('phase3', {}), lang, 3),
    ]

    # Personalise all free-text strings in phases
    path['phases'] = _personalise(path['phases'], name, age, location, skills_str)

    return path


# ── ROUTE ────────────────────────────────────────────────────────
@roadmap_bp.route('/api/generate-roadmap', methods=['POST'])
def generate_roadmap():
    """
    Query Supabase for matching jobs based on user profile.
    Returns 3 career path objects in the shape the JS frontend expects.

    Request body (JSON):
      { "profile": { name, age, location, education, interest, skills[], income_mode },
        "lang": "en" | "bm" }

    Response (JSON):
      { "careerPaths": [ ...3 paths... ] }   on success
      { "error": "..." }                     on failure
    """
    import requests as req_lib

    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    if not SUPABASE_URL:
        return jsonify({'error': 'SUPABASE_URL not configured'}), 500

    data    = request.get_json(force=True, silent=True) or {}
    profile = data.get('profile', {})
    lang    = data.get('lang', 'en')

    if not profile.get('name'):
        return jsonify({'error': 'Missing profile data'}), 400

    interest  = profile.get('interest', 'biz')
    user_edu  = profile.get('education', 'primary')
    user_age  = profile.get('age', '18-22')

    try:
        # ── 1. Fetch jobs for this interest category ──────────────
        # Pull up to 20 rows so we have enough to filter and rank
        url = (
            f"{SUPABASE_URL}/rest/v1/jobs"
            f"?category=eq.{interest}"
            f"&limit=20"
            f"&select=*"
        )
        res = req_lib.get(url, headers=_supabase_headers(), timeout=8)
        if not res.ok:
            current_app.logger.error(f'[NAIK] Supabase error {res.status_code}: {res.text[:200]}')
            return jsonify({'error': f'Database error {res.status_code}'}), 502

        jobs = res.json()

        if not jobs:
            # Fallback: try any category if no jobs found for this interest
            url_fallback = (
                f"{SUPABASE_URL}/rest/v1/jobs"
                f"?limit=20"
                f"&select=*"
            )
            res2 = req_lib.get(url_fallback, headers=_supabase_headers(), timeout=8)
            jobs = res2.json() if res2.ok else []
        elif len(jobs) < 3:
            # We have some results but fewer than 3 — pad with jobs from other categories
            url_pad = (
                f"{SUPABASE_URL}/rest/v1/jobs"
                f"?category=neq.{interest}"
                f"&limit=10"
                f"&select=*"
            )
            res_pad = req_lib.get(url_pad, headers=_supabase_headers(), timeout=8)
            if res_pad.ok:
                jobs = jobs + res_pad.json()

        # ── 2. Filter by eligibility ──────────────────────────────
        eligible = [
            j for j in jobs
            if _education_ok(j.get('education_min', 'primary'), user_edu)
            and _age_ok(j.get('min_age', 16), user_age)
            # If job has hard cert requirement, only include if user already has relevant education
            and (not j.get('cert_required') or user_edu in ['spm', 'spm_incomplete'])
        ]

        # If filtering removed everything OR left too few, progressively relax constraints
        if len(eligible) < 3:
            # Relax: ignore cert requirement
            eligible = [
                j for j in jobs
                if _education_ok(j.get('education_min', 'primary'), user_edu)
                and _age_ok(j.get('min_age', 16), user_age)
            ]

        if len(eligible) < 3:
            # Relax further: ignore age constraint too
            eligible = [
                j for j in jobs
                if _education_ok(j.get('education_min', 'primary'), user_edu)
            ]

        # If still too few, use all jobs in this category
        if not eligible:
            eligible = jobs

        # ── 3. Score & rank ───────────────────────────────────────
        scored = sorted(eligible, key=lambda j: _score_job(j, profile), reverse=True)
        top3   = scored[:3]

        if not top3:
            return jsonify({'error': 'No matching jobs found in database. Please seed your Supabase jobs table.'}), 404

        # ── 4. Convert to career path format ─────────────────────
        career_paths = [
            _job_to_career_path(job, idx, profile, lang)
            for idx, job in enumerate(top3)
        ]

        current_app.logger.info(
            f'[NAIK] ✅ Returned {len(career_paths)} paths for '
            f'{profile.get("name")} / interest={interest} / lang={lang}'
        )
        return jsonify({'careerPaths': career_paths})

    except req_lib.Timeout:
        current_app.logger.warning('[NAIK] Supabase request timed out')
        return jsonify({'error': 'Database timed out'}), 504
    except Exception as e:
        current_app.logger.error(f'[NAIK] Unexpected error: {e}')
        return jsonify({'error': str(e)}), 500


# ── HOW TO REGISTER ──────────────────────────────────────────────
# from roadmap_backend import roadmap_bp
# app.register_blueprint(roadmap_bp)