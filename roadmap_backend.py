"""
roadmap_backend.py  (v3 — Full quiz + recommendations + saved jobs)
────────────────────────────────────────────────────────────────────
New routes added:
  POST /api/quiz/save           → save quiz results for logged-in user
  POST /api/recommendations     → return top 3 jobs based on saved quiz results
  POST /api/jobs/save           → save a job for the logged-in user
  GET  /api/jobs/saved          → return all saved jobs for logged-in user
  POST /api/generate-roadmap    → existing roadmap generation (unchanged)

WHY-FIT PERSONALISATION:
  _generate_why_fit_dynamic() builds personalised "why it fits you"
  text at runtime based on actual quiz answers (q_people, q_outdoor,
  q_digital, q_creative, income_mode, skills, education) rather than
  a fixed template. This makes each recommendation feel personalised.

SCORING LOGIC:
  Scores jobs on:
    1. Category match (+10)
    2. Skills affinity (+3 per matching skill)
    3. Income mode fit (entry vs target salary)
    4. Poverty exit score weight (+0.5 per point)
    5. Quiz preference alignment (q_people, q_outdoor, q_digital, q_creative etc → +2 each)
    6. Physical/digital fit penalties (-3 for mismatches)
"""

import os
import re
from flask import Blueprint, request, jsonify, session, current_app

roadmap_bp = Blueprint('roadmap', __name__)

# Education level ordering
EDUCATION_ORDER = ['primary', 'secondary_incomplete', 'spm_incomplete', 'spm']

# Skill → category affinities
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

# Quiz preference → job affinity mapping
QUIZ_AFFINITY_MAP = {
    'q_people':    ('people_work', 3),
    'q_outdoor':   ('outdoor',     3),
    'q_creative':  ('creative',    3),
    'q_flexible':  ('flexible',    3),
    'q_leadership':('leadership',  3),
}


# ── HELPERS ────────────────────────────────────────────────────

def _supabase_headers():
    key = os.environ.get('SUPABASE_KEY', '')
    return {
        'apikey':        key,
        'Authorization': f'Bearer {key}',
        'Content-Type':  'application/json',
    }


def _supabase_url():
    return os.environ.get('SUPABASE_URL', '')


def _education_ok(job_edu_min, user_edu):
    try:
        return EDUCATION_ORDER.index(user_edu) >= EDUCATION_ORDER.index(job_edu_min)
    except ValueError:
        return True


def _age_ok(job_min_age, user_age_range):
    range_min = {'15-17': 15, '18-22': 18, '23-29': 23, '30+': 30}.get(user_age_range, 18)
    return range_min >= job_min_age


def _score_job(job, quiz_result):
    """
    Score a job's relevance to this user based on full quiz results.
    Higher score = better match.
    """
    score = 0
    user_skills   = quiz_result.get('skills') or []
    user_category = quiz_result.get('interest', 'biz')
    income_mode   = quiz_result.get('income_mode', 'immediate')
    job_affinities = job.get('quiz_affinity') or []

    # 1. Category match (strongest signal)
    if job.get('category') == user_category:
        score += 10

    # 2. Skill affinity boost
    for skill in user_skills:
        if user_category in SKILL_CATEGORY_AFFINITY.get(skill, []):
            score += 3
        # Also check job's direct skills_affinity field
        if skill in (job.get('skills_affinity') or []):
            score += 2

    # 3. Income mode fit
    if income_mode == 'immediate':
        # Prefer higher entry salary (poverty exit focus)
        score += max(0, (job.get('entry_salary_min', 1400) - 1400) // 100)
    else:
        # Prefer higher target salary (growth potential)
        score += max(0, (job.get('target_salary_max', 3000) - 3000) // 200)

    # 4. Poverty exit score
    score += job.get('poverty_exit_score', 5) * 0.5

    # 5. Quiz preference alignment
    for quiz_field, (affinity_tag, threshold) in QUIZ_AFFINITY_MAP.items():
        quiz_val = quiz_result.get(quiz_field)
        if quiz_val is not None and quiz_val >= threshold:
            if affinity_tag in job_affinities:
                score += 2



    # 7. Growth willingness → weight poverty exit more
    q_growth = quiz_result.get('q_growth')
    if q_growth is not None and q_growth >= 3:
        score += job.get('poverty_exit_score', 5) * 0.3

    # 8. Physical mismatch penalties
    q_outdoor = quiz_result.get('q_outdoor', 2)
    if job.get('physically_demanding') and q_outdoor < 2:
        score -= 3
    if not job.get('physically_demanding') and q_outdoor >= 4:
        score -= 1  # minor penalty — outdoor-lover might get bored


    return score


def _generate_why_fit_dynamic(job, quiz_result, lang):
    """
    Generate personalised "why it fits you" bullets based on actual quiz answers
    AND job-specific attributes. Each job gets distinct, tailored reasons.
    """
    name        = quiz_result.get('name', 'You' if lang == 'en' else 'Anda')
    user_skills = quiz_result.get('skills') or []
    income_mode = quiz_result.get('income_mode', 'immediate')
    q_people    = quiz_result.get('q_people', 2)
    q_outdoor   = quiz_result.get('q_outdoor', 2)
    q_creative  = quiz_result.get('q_creative', 2)
    q_flexible  = quiz_result.get('q_flexible', 2)
    q_growth    = quiz_result.get('q_growth', 2)
    q_leadership = quiz_result.get('q_leadership', 2)
    education   = quiz_result.get('education', 'spm')
    job_affinities = job.get('quiz_affinity') or []
    job_skills_affinity = job.get('skills_affinity') or []
    job_category = job.get('category', '')
    work_type = job.get('work_type', job.get('income_type', 'fixed'))
    entry_min = job.get('entry_salary_min', 1400)
    target_max = job.get('target_salary_max', 4000)
    timeline = job.get('timeline_years', '2–3')
    poverty_score = job.get('poverty_exit_score', 5)
    cert_required = job.get('cert_required', False)
    physically_demanding = job.get('physically_demanding', False)
    internet_required = job.get('internet_required', False)
    title = job.get('title_en', 'this role')
    tagline = job.get('tagline_en', '')

    reasons = []

    if lang == 'en':
        skill_names = {
            'customer_service': 'customer service experience',
            'cooking': 'cooking skills',
            'driving': 'driving licence',
            'computer_basic': 'computer skills',
            'social_media': 'social media skills',
            'sales': 'sales experience',
            'caregiving': 'caregiving experience',
            'manual_labor': 'physical/manual work experience',
        }

        # 1. Matching skills — name the specific skills that match THIS job
        matching_skills = [s for s in user_skills if s in job_skills_affinity]
        if matching_skills:
            skill_labels = [skill_names.get(s, s) for s in matching_skills[:2]]
            reasons.append(f"your {' and '.join(skill_labels)} is a direct match for what {title} requires")
        elif user_skills:
            # Skills don't directly match but explain category fit
            first_skill = skill_names.get(user_skills[0], user_skills[0])
            reasons.append(f"your background in {first_skill} gives you a head start in this field")

        # 2. Personality/preference alignment — specific to this job's characteristics
        if q_people >= 3 and 'people_work' in job_affinities:
            reasons.append(f"you enjoy working with people — {title} is customer/people-facing every single day")
        elif q_people < 2 and 'people_work' not in job_affinities:
            reasons.append(f"this role suits you — it's mostly independent work without constant customer interaction")

        if q_outdoor >= 3 and physically_demanding:
            reasons.append(f"you prefer being active and on your feet — {title} is a physically engaged role, not desk-bound")
        elif q_outdoor < 2 and not physically_demanding:
            reasons.append(f"this is an indoor/seated role — suits your preference for non-physical work")

        if q_creative >= 3 and 'creative' in job_affinities:
            reasons.append(f"your creative inclination is directly valued in {title} — creativity is core to the role, not optional")

        if q_flexible >= 3 and job.get('work_type') in ('part-time', 'freelance'):
            reasons.append(f"you said flexibility matters — {title} is {job.get('work_type', 'flexible')}, so you control your schedule")
        elif q_flexible < 2 and job.get('work_type') == 'full-time':
            reasons.append(f"you prefer structure — this is a fixed full-time role with clear working hours")

        if q_leadership >= 3 and 'leadership' in job_affinities:
            reasons.append(f"you're growth-oriented — the {title} path has a clear leadership/management track")

        # 3. Income mode fit — specific to this job's salary profile
        if income_mode == 'immediate':
            reasons.append(f"you need income now — {title} starts at RM{entry_min:,}/month and can be started quickly")
        else:
            reasons.append(f"you're focused on long-term growth — this path reaches RM{target_max:,}/month within {timeline} years")

        # 4. Poverty exit / stability — job-specific
        if poverty_score >= 8:
            reasons.append(f"{title} has one of the highest demand ratings — stable hiring year-round, very low redundancy risk")
        elif poverty_score >= 6:
            reasons.append(f"this is a stable, in-demand role — not a dying industry, not a seasonal gig")

        # 5. Education/certification fit
        if not cert_required:
            edu_labels = {
                'primary': 'primary school level',
                'secondary_incomplete': 'secondary school background',
                'spm_incomplete': 'partial SPM',
                'spm': 'SPM',
            }
            edu_label = edu_labels.get(education, 'your education level')
            reasons.append(f"no cert or degree required — your {edu_label} is sufficient to apply now")

        # 6. Internet/remote fit
        if internet_required and q_flexible >= 3:
            reasons.append(f"this role can be done remotely — suits your preference for flexible working arrangements")

        if not reasons:
            reasons = ["this is a strong match based on your quiz answers"]

        # Build paragraph — lead with name, keep it specific
        text = f"{name}, {reasons[0]}"
        for r in reasons[1:3]:
            text += f". Also, {r}"
        text += "."

        if income_mode == 'immediate':
            pass  # income reason already added above

        return text

    else:  # Bahasa Malaysia
        title_bm = job.get('title_bm', title)
        skill_names_bm = {
            'customer_service': 'pengalaman perkhidmatan pelanggan',
            'cooking': 'kemahiran memasak',
            'driving': 'lesen memandu',
            'computer_basic': 'kemahiran komputer',
            'social_media': 'kemahiran media sosial',
            'sales': 'pengalaman jualan',
            'caregiving': 'pengalaman penjagaan',
            'manual_labor': 'pengalaman kerja fizikal',
        }
        matching_skills = [s for s in user_skills if s in job_skills_affinity]
        if matching_skills:
            skill_labels = [skill_names_bm.get(s, s) for s in matching_skills[:2]]
            reasons.append(f"{' dan '.join(skill_labels)} anda sesuai secara langsung dengan keperluan {title_bm}")
        if q_people >= 3 and 'people_work' in job_affinities:
            reasons.append(f"anda suka bekerja dengan orang — {title_bm} berhadapan pelanggan setiap hari")
        if q_outdoor >= 3 and physically_demanding:
            reasons.append(f"anda selesa bergerak aktif — {title_bm} adalah kerja fizikal, bukan kerja meja")
        elif q_outdoor < 2 and not physically_demanding:
            reasons.append(f"ini adalah kerja dalam — sesuai dengan pilihan anda untuk kerja tidak fizikal")
        if q_creative >= 3 and 'creative' in job_affinities:
            reasons.append(f"kreativiti anda sangat dihargai dalam {title_bm}")
        if q_flexible >= 3 and job.get('work_type') in ('part-time', 'freelance'):
            reasons.append(f"anda perlukan fleksibiliti — {title_bm} adalah {job.get('work_type', 'fleksibel')}")
        if q_growth >= 3:
            reasons.append(f"anda bersedia belajar — laluan ini boleh capai RM{target_max:,}/bulan dalam {timeline} tahun")
        if income_mode == 'immediate':
            reasons.append(f"anda perlukan pendapatan segera — {title_bm} bermula RM{entry_min:,}/bulan")
        else:
            reasons.append(f"dengan peningkatan kemahiran, anda boleh capai RM{target_max:,}/bulan dalam {timeline} tahun")
        if poverty_score >= 8:
            reasons.append(f"{title_bm} mempunyai permintaan tinggi — pengambilan stabil sepanjang tahun")
        if not cert_required:
            reasons.append(f"tiada sijil diperlukan — kelayakan anda sudah mencukupi untuk memohon sekarang")
        if not reasons:
            reasons = ["ini adalah padanan yang kuat berdasarkan jawapan kuiz anda"]
        text = f"{name}, {reasons[0]}"
        for r in reasons[1:3]:
            text += f". Juga, {r}"
        text += "."
        return text


def _build_income_ladder(job, lang):
    ladder = job.get('income_ladder') or []
    result = []
    for row in ladder:
        result.append({
            'stage':   row.get(f'stage_{lang}', row.get('stage_en', '')),
            'role':    row.get(f'role_{lang}',  row.get('role_en', '')),
            'income':  row.get('income', ''),
            'current': row.get('current', False),
            'tip':     row.get(f'tip_{lang}',   row.get('tip_en', '')),
        })
    return result


def _fill_placeholders(text, name, age, location, skills_str):
    if not isinstance(text, str):
        return text
    return (text
            .replace('{name}',     name)
            .replace('{age}',      age)
            .replace('{location}', location)
            .replace('{skills}',   skills_str))


def _personalise(obj, name, age, location, skills_str):
    if isinstance(obj, str):
        return _fill_placeholders(obj, name, age, location, skills_str)
    if isinstance(obj, list):
        return [_personalise(i, name, age, location, skills_str) for i in obj]
    if isinstance(obj, dict):
        return {k: _personalise(v, name, age, location, skills_str) for k, v in obj.items()}
    return obj


def _job_to_rec(job, idx, quiz_result, lang):
    """Convert a DB job row into the recommendation card shape."""
    option_ids  = ['A', 'B', 'C']
    name        = quiz_result.get('name', 'You')
    age         = quiz_result.get('age', '')
    location    = 'Malaysia'
    skills_list = quiz_result.get('skills') or []
    skills_str  = ', '.join(skills_list) if skills_list else ('your skills' if lang == 'en' else 'kemahiran anda')

    path = {
        'id':           job.get('id'),
        'emoji':        job.get('emoji', '💼'),
        'title':        job.get(f'title_{lang}', job.get('title_en', '')),
        'tagline':      job.get(f'tagline_{lang}', job.get('tagline_en', '')),
        # Use duties (what you actually do) as the job description shown on cards
        'description':  job.get(f'duties_{lang}', job.get('duties_en', job.get(f'description_{lang}', job.get('description_en', job.get('tagline_en', ''))))),
        'targetJob':    job.get(f'target_job_{lang}', job.get('target_job_en', '')),
        'entryJob':     job.get(f'entry_job_{lang}', job.get('entry_job_en', '')),
        'targetSalary': f"RM{job.get('target_salary_min', 2500):,}–{job.get('target_salary_max', 4000):,}/{'month' if lang == 'en' else 'bulan'}",
        'entrySalary':  f"RM{job.get('entry_salary_min', 1400):,}–{job.get('entry_salary_max', 1800):,}/{'month' if lang == 'en' else 'bulan'}",
        'timeline':     f"{job.get('timeline_years', '2–3')} {'years' if lang == 'en' else 'tahun'}",
        'safetyRating': job.get(f'safety_rating_{lang}', job.get('safety_rating_en', 'Steady Growth')),
        'incomeType':   job.get('income_type', 'fixed'),
        'incomeLadder': _build_income_ladder(job, lang),
        'jobSearchKeywords': job.get('jobstreet_keywords') or [],

        # Dynamic personalised why-fit
        'whyFitPersonalised': _generate_why_fit_dynamic(job, quiz_result, lang),
        'whyFitTags': _build_why_fit_tags(job, quiz_result, lang),
    }

    # Personalise the income ladder
    path['incomeLadder'] = _personalise(path['incomeLadder'], name, age, location, skills_str)

    return path


def _build_why_fit_tags(job, quiz_result, lang):
    """Build short bullet-point style phrases for why this job fits the user."""
    tags = []
    user_skills = quiz_result.get('skills') or []
    income_mode = quiz_result.get('income_mode', 'immediate')
    job_affinities = job.get('quiz_affinity') or []
    q_outdoor = quiz_result.get('q_outdoor', 2)
    q_people  = quiz_result.get('q_people', 2)

    if lang == 'en':
        if not job.get('cert_required'):
            tags.append('No cert or degree required')
        edu_min = job.get('education_min', 'primary')
        if edu_min in ['primary', 'secondary_incomplete']:
            tags.append('Accessible with your education level')
        if any(s in (job.get('skills_affinity') or []) for s in user_skills):
            tags.append('Matches skills you already have')
        if income_mode == 'immediate':
            tags.append(f"Start earning RM{job.get('entry_salary_min', 1500):,}/month quickly")
        else:
            tags.append(f"Grow to RM{job.get('target_salary_max', 4000):,}/month with upskilling")
        if job.get('poverty_exit_score', 5) >= 7:
            tags.append('High demand — stable hiring all year')
        if job.get('physically_demanding') and q_outdoor >= 3:
            tags.append('Physical work suits your preference')
        elif not job.get('physically_demanding') and q_outdoor < 2:
            tags.append('Indoor work — suits your style')
        if q_people >= 3 and 'people_work' in job_affinities:
            tags.append('People-facing role — suits your personality')
        if job.get('income_type') == 'mixed':
            tags.append('Overtime available — earn more when you work more')
    else:
        if not job.get('cert_required'):
            tags.append('Tiada sijil atau ijazah diperlukan')
        if any(s in (job.get('skills_affinity') or []) for s in user_skills):
            tags.append('Sesuai dengan kemahiran anda')
        if income_mode == 'immediate':
            tags.append(f"Mula menjana RM{job.get('entry_salary_min', 1500):,}/bulan dengan cepat")
        else:
            tags.append(f"Capai RM{job.get('target_salary_max', 4000):,}/bulan dengan peningkatan kemahiran")
        if job.get('poverty_exit_score', 5) >= 7:
            tags.append('Permintaan tinggi — pengambilan stabil sepanjang tahun')

    return tags[:5]  # max 5 bullet points


# ── ROUTE: SAVE QUIZ RESULTS ─────────────────────────────────────

@roadmap_bp.route('/api/quiz/save', methods=['POST'])
def save_quiz():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data    = request.get_json(force=True, silent=True) or {}
    profile = data.get('profile', {})
    lang    = data.get('lang', 'en')

    # Build the quiz_results row
    row = {
        'user_id':     user_id,
        'interest':    profile.get('interest'),
        'income_mode': profile.get('income_mode'),
        'education':   profile.get('education'),
        'skills':      profile.get('skills') or [],
        # Slider answers (q_digital and q_ambition removed from quiz)
        'q_people':    profile.get('q_people'),
        'q_outdoor':   profile.get('q_outdoor'),
        'q_creative':  profile.get('q_creative'),
        'q_flexible':  profile.get('q_flexible'),
        'q_growth':    profile.get('q_growth'),
        'q_leadership':profile.get('q_leadership'),
        'profile_summary': {
            'interest':    profile.get('interest'),
            'income_mode': profile.get('income_mode'),
            'education':   profile.get('education'),
            'lang':        lang,
        }
    }

    try:
        # Supabase upsert: on_conflict MUST be a query param, not a header
        url = f"{_supabase_url()}/rest/v1/quiz_results?on_conflict=user_id"
        res = req_lib.post(
            url,
            json=row,
            headers={
                **_supabase_headers(),
                'Prefer': 'resolution=merge-duplicates,return=minimal',
            },
            timeout=8
        )
        if not res.ok:
            current_app.logger.warning(f'[NAIK] Quiz upsert status {res.status_code}: {res.text}')
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f'[NAIK] Quiz save error: {e}')
        return jsonify({'error': str(e)}), 500


# ── ROUTE: GET PERSONALISED RECOMMENDATIONS ──────────────────────

@roadmap_bp.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json(force=True, silent=True) or {}
    lang = data.get('lang', 'en')

    try:
        # 1. Fetch quiz results for this user
        qr_url = (
            f"{_supabase_url()}/rest/v1/quiz_results"
            f"?user_id=eq.{user_id}&select=*&limit=1"
        )
        qr_res = req_lib.get(qr_url, headers=_supabase_headers(), timeout=8)
        qr_rows = qr_res.json() if qr_res.ok else []

        if not qr_rows:
            return jsonify({'jobs': [], 'savedJobIds': [], 'error': 'No quiz results found'})

        quiz_result = qr_rows[0]

        # Also get user name
        user_url = f"{_supabase_url()}/rest/v1/users?id=eq.{user_id}&select=name&limit=1"
        user_res = req_lib.get(user_url, headers=_supabase_headers(), timeout=8)
        if user_res.ok and user_res.json():
            quiz_result['name'] = user_res.json()[0].get('name', 'You')

        interest = quiz_result.get('interest', 'biz')
        user_edu = quiz_result.get('education', 'primary')
        user_age = quiz_result.get('age', '18-22')

        # 2. Fetch jobs for this category
        jobs_url = (
            f"{_supabase_url()}/rest/v1/jobs"
            f"?category=eq.{interest}&limit=20&select=*"
        )
        jobs_res = req_lib.get(jobs_url, headers=_supabase_headers(), timeout=8)
        jobs = jobs_res.json() if jobs_res.ok else []

        # Pad if fewer than 3
        if len(jobs) < 3:
            pad_url = f"{_supabase_url()}/rest/v1/jobs?limit=20&select=*"
            pad_res = req_lib.get(pad_url, headers=_supabase_headers(), timeout=8)
            if pad_res.ok:
                existing_ids = {j['id'] for j in jobs}
                for j in pad_res.json():
                    if j['id'] not in existing_ids:
                        jobs.append(j)

        # 3. Filter by eligibility
        eligible = [
            j for j in jobs
            if _education_ok(j.get('education_min', 'primary'), user_edu)
            and _age_ok(j.get('min_age', 16), user_age)
        ]
        if not eligible:
            eligible = jobs

        # 4. Score & rank
        scored = sorted(eligible, key=lambda j: _score_job(j, quiz_result), reverse=True)
        top3   = scored[:3]

        # 5. Get user's saved job IDs
        sj_url = f"{_supabase_url()}/rest/v1/saved_jobs?user_id=eq.{user_id}&select=job_id"
        sj_res = req_lib.get(sj_url, headers=_supabase_headers(), timeout=8)
        saved_ids = [r['job_id'] for r in sj_res.json()] if sj_res.ok else []

        # 6. Convert to rec format
        recs = [_job_to_rec(job, idx, quiz_result, lang) for idx, job in enumerate(top3)]

        return jsonify({'jobs': recs, 'savedJobIds': saved_ids})

    except Exception as e:
        current_app.logger.error(f'[NAIK] Recommendations error: {e}')
        return jsonify({'error': str(e)}), 500


# ── ROUTE: GET QUIZ RESULTS (for explore page why-fit) ───────────

@roadmap_bp.route('/api/quiz/results', methods=['GET'])
def get_quiz_results():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'quiz': None})

    try:
        qr_url = (
            f"{_supabase_url()}/rest/v1/quiz_results"
            f"?user_id=eq.{user_id}&select=*&limit=1"
        )
        qr_res = req_lib.get(qr_url, headers=_supabase_headers(), timeout=8)
        qr_rows = qr_res.json() if qr_res.ok else []

        if not qr_rows:
            return jsonify({'quiz': None})

        quiz = qr_rows[0]

        # Also get user name
        user_url = f"{_supabase_url()}/rest/v1/users?id=eq.{user_id}&select=name&limit=1"
        user_res = req_lib.get(user_url, headers=_supabase_headers(), timeout=8)
        if user_res.ok and user_res.json():
            quiz['name'] = user_res.json()[0].get('name', 'You')

        # Get saved job IDs
        sj_url = f"{_supabase_url()}/rest/v1/saved_jobs?user_id=eq.{user_id}&select=job_id"
        sj_res = req_lib.get(sj_url, headers=_supabase_headers(), timeout=8)
        saved_ids = [r['job_id'] for r in sj_res.json()] if sj_res.ok else []

        return jsonify({'quiz': quiz, 'savedJobIds': saved_ids})
    except Exception as e:
        return jsonify({'quiz': None, 'error': str(e)})


# ── ROUTE: GET WHY-FIT FOR A SPECIFIC JOB ────────────────────────

@roadmap_bp.route('/api/jobs/why-fit', methods=['POST'])
def get_why_fit():
    """Return why-fit bullets for a specific job based on user's quiz results."""
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'whyFit': [], 'motivation': ''})

    data   = request.get_json(force=True, silent=True) or {}
    job_id = data.get('job_id')
    lang   = data.get('lang', 'en')

    if not job_id:
        return jsonify({'whyFit': [], 'motivation': ''})

    try:
        # Fetch quiz results
        qr_url = f"{_supabase_url()}/rest/v1/quiz_results?user_id=eq.{user_id}&select=*&limit=1"
        qr_res = req_lib.get(qr_url, headers=_supabase_headers(), timeout=8)
        qr_rows = qr_res.json() if qr_res.ok else []
        if not qr_rows:
            return jsonify({'whyFit': [], 'motivation': ''})

        quiz = qr_rows[0]

        # Get user name
        user_url = f"{_supabase_url()}/rest/v1/users?id=eq.{user_id}&select=name&limit=1"
        user_res = req_lib.get(user_url, headers=_supabase_headers(), timeout=8)
        if user_res.ok and user_res.json():
            quiz['name'] = user_res.json()[0].get('name', 'You')

        # Fetch job
        job_url = f"{_supabase_url()}/rest/v1/jobs?id=eq.{job_id}&select=*&limit=1"
        job_res = req_lib.get(job_url, headers=_supabase_headers(), timeout=8)
        jobs = job_res.json() if job_res.ok else []
        if not jobs:
            return jsonify({'whyFit': [], 'motivation': ''})

        job = jobs[0]
        why_fit_text = _generate_why_fit_dynamic(job, quiz, lang)
        why_fit_tags = _build_why_fit_tags(job, quiz, lang)

        name = quiz.get('name', 'You')
        age = quiz.get('age', '')
        location = 'Malaysia'
        skills_list = quiz.get('skills') or []
        skills_str = ', '.join(skills_list) if skills_list else 'your skills'
        motivation = _fill_placeholders(
            job.get(f'motivation_{lang}', job.get('motivation_en', '')),
            name, age, location, skills_str
        )

        return jsonify({
            'whyFitPersonalised': why_fit_text,
            'whyFitTags': why_fit_tags,
            'motivation': motivation,
        })

    except Exception as e:
        return jsonify({'whyFit': [], 'motivation': '', 'error': str(e)})


# ── ROUTE: SAVE A JOB ────────────────────────────────────────────

@roadmap_bp.route('/api/jobs/save', methods=['POST'])
def save_job():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data   = request.get_json(force=True, silent=True) or {}
    job_id = data.get('job_id')
    if not job_id:
        return jsonify({'error': 'Missing job_id'}), 400

    try:
        url = f"{_supabase_url()}/rest/v1/saved_jobs"
        res = req_lib.post(
            url,
            json={'user_id': user_id, 'job_id': job_id},
            headers={**_supabase_headers(), 'Prefer': 'resolution=ignore-duplicates'},
            timeout=8
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ROUTE: GET SAVED JOBS ─────────────────────────────────────────

@roadmap_bp.route('/api/jobs/saved', methods=['GET'])
def get_saved_jobs():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    try:
        # Join saved_jobs with jobs
        url = (
            f"{_supabase_url()}/rest/v1/saved_jobs"
            f"?user_id=eq.{user_id}&select=job_id,jobs(*)"
        )
        res = req_lib.get(url, headers=_supabase_headers(), timeout=8)
        if not res.ok:
            return jsonify({'jobs': []})
        rows = res.json()
        jobs = [r.get('jobs') or {} for r in rows if r.get('jobs')]
        return jsonify({'jobs': jobs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ROUTE: UNSAVE A JOB ──────────────────────────────────────────

@roadmap_bp.route('/api/jobs/unsave', methods=['POST'])
def unsave_job():
    import requests as req_lib

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data   = request.get_json(force=True, silent=True) or {}
    job_id = data.get('job_id')
    if not job_id:
        return jsonify({'error': 'Missing job_id'}), 400

    try:
        url = (
            f"{_supabase_url()}/rest/v1/saved_jobs"
            f"?user_id=eq.{user_id}&job_id=eq.{job_id}"
        )
        res = req_lib.delete(url, headers=_supabase_headers(), timeout=8)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ROUTE: GENERATE ROADMAP (existing, unchanged interface) ──────

@roadmap_bp.route('/api/generate-roadmap', methods=['POST'])
def generate_roadmap():
    """
    Generate a career roadmap for a saved job.
    Pulls quiz results from DB to personalise content.
    """
    import requests as req_lib

    SUPABASE = _supabase_url()
    if not SUPABASE:
        return jsonify({'error': 'SUPABASE_URL not configured'}), 500

    data    = request.get_json(force=True, silent=True) or {}
    profile = data.get('profile', {})
    lang    = data.get('lang', 'en')
    job_id  = data.get('job_id')

    # If job_id provided, load quiz results from DB for personalisation
    user_id = session.get('user_id')
    if user_id and not profile.get('name'):
        try:
            qr_url = f"{SUPABASE}/rest/v1/quiz_results?user_id=eq.{user_id}&select=*&limit=1"
            qr_res = req_lib.get(qr_url, headers=_supabase_headers(), timeout=8)
            if qr_res.ok and qr_res.json():
                qr = qr_res.json()[0]
                profile.update({
                    'age':        qr.get('age', '18-22'),
                    'education':  qr.get('education', 'spm'),
                    'interest':   qr.get('interest', 'biz'),
                    'skills':     qr.get('skills') or [],
                    'income_mode':qr.get('income_mode', 'immediate'),
                })
            user_url = f"{SUPABASE}/rest/v1/users?id=eq.{user_id}&select=name&limit=1"
            user_res = req_lib.get(user_url, headers=_supabase_headers(), timeout=8)
            if user_res.ok and user_res.json():
                profile['name'] = user_res.json()[0].get('name', 'You')
        except Exception:
            pass

    if not profile.get('name'):
        profile['name'] = 'You' if lang == 'en' else 'Anda'

    interest  = profile.get('interest', 'biz')
    user_edu  = profile.get('education', 'primary')
    user_age  = profile.get('age', '18-22')

    try:
        # Fetch specific job if job_id provided, else fetch by interest
        if job_id:
            url = f"{SUPABASE}/rest/v1/jobs?id=eq.{job_id}&select=*&limit=1"
        else:
            url = f"{SUPABASE}/rest/v1/jobs?category=eq.{interest}&limit=20&select=*"

        res = req_lib.get(url, headers=_supabase_headers(), timeout=8)
        if not res.ok:
            return jsonify({'error': f'Database error {res.status_code}'}), 502

        jobs = res.json()
        if not jobs:
            return jsonify({'error': 'No matching jobs found'}), 404

        if job_id:
            top3 = jobs[:1]
        else:
            eligible = [
                j for j in jobs
                if _education_ok(j.get('education_min', 'primary'), user_edu)
                and _age_ok(j.get('min_age', 16), user_age)
            ]
            scored = sorted(eligible or jobs, key=lambda j: _score_job(j, profile), reverse=True)
            top3 = scored[:3]

        career_paths = [_job_to_career_path(job, idx, profile, lang) for idx, job in enumerate(top3)]
        return jsonify({'careerPaths': career_paths})

    except req_lib.Timeout:
        return jsonify({'error': 'Database timed out'}), 504
    except Exception as e:
        current_app.logger.error(f'[NAIK] Roadmap error: {e}')
        return jsonify({'error': str(e)}), 500


def _build_phase(phase_data, lang, phase_num, courses_override=None):
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
    if phase_num == 1:
        phase['immediateJobKeywords'] = phase_data.get('immediate_job_keywords', [])
    if phase_num == 2:
        raw_courses = courses_override or phase_data.get('courses', [])
        phase['courses'] = [
            {'name': c.get('name', ''), 'provider': c.get('provider', ''), 'url': c.get('url', ''),
             'duration': c.get(f'duration_{lang}', c.get('duration_en', '')), 'free': c.get('free', True)}
            for c in raw_courses
        ]
    if phase_num == 3:
        c = phase_data.get('course', {})
        if c:
            phase['course'] = {'name': c.get('name', ''), 'provider': c.get('provider', ''), 'url': c.get('url', ''),
                               'duration': c.get(f'duration_{lang}', c.get('duration_en', '')), 'free': c.get('free', True)}
    return phase


def _job_to_career_path(job, idx, profile, lang):
    option_ids   = ['A', 'B', 'C']
    name         = profile.get('name', 'You' if lang == 'en' else 'Anda')
    age          = profile.get('age', '')
    location     = profile.get('location', 'Malaysia')
    skills_list  = profile.get('skills') or []
    skills_str   = ', '.join(skills_list) if skills_list else ('your skills' if lang == 'en' else 'kemahiran anda')

    path = {
        'id':           option_ids[idx] if idx < 3 else str(idx + 1),
        'emoji':        job.get('emoji', '💼'),
        'title':        f"{job.get('emoji','💼')} Option {option_ids[idx] if idx<3 else idx+1}: {job.get(f'title_{lang}', job.get('title_en',''))}",
        'targetJob':    job.get(f'target_job_{lang}',   job.get('target_job_en', '')),
        'targetSalary': f"RM{job.get('target_salary_min',2500):,}–{job.get('target_salary_max',4000):,}/{'month' if lang=='en' else 'bulan'}",
        'entryJob':     job.get(f'entry_job_{lang}',    job.get('entry_job_en', '')),
        'entrySalary':  f"RM{job.get('entry_salary_min',1400):,}–{job.get('entry_salary_max',1800):,}/{'month' if lang=='en' else 'bulan'}",
        'timeline':     f"{job.get('timeline_years','2–3')} {'years' if lang=='en' else 'tahun'}",
        'tagline':      job.get(f'tagline_{lang}', job.get('tagline_en', '')),
        'safetyRating': job.get(f'safety_rating_{lang}', job.get('safety_rating_en', 'Steady Growth')),
        'incomeType':   job.get('income_type', 'fixed'),
        'jobSearchKeywords': job.get('jobstreet_keywords') or [],
        'whyFit':       _generate_why_fit_dynamic(job, profile, lang),
        'whyFitTags':   _build_why_fit_tags(job, profile, lang),
        'jobDesc':      job.get(f'duties_{lang}', job.get('duties_en', job.get(f'description_{lang}', job.get('description_en', '')))),
        'motivation':   _fill_placeholders(job.get(f'motivation_{lang}', job.get('motivation_en', '')), name, age, location, skills_str),
        'incomeLadder': _build_income_ladder(job, lang),
        'phases': [
            _build_phase(job.get('phase1', {}), lang, 1),
            _build_phase(job.get('phase2', {}), lang, 2, courses_override=job.get('courses', [])),
            _build_phase(job.get('phase3', {}), lang, 3),
        ],
    }
    path['phases'] = _personalise(path['phases'], name, age, location, skills_str)
    return path

@roadmap_bp.route('/api/jobs/all', methods=['GET'])
def get_all_jobs():
    import requests as req_lib
    try:
        url = f"{_supabase_url()}/rest/v1/jobs?select=*&limit=100&order=poverty_exit_score.desc"
        res = req_lib.get(url, headers=_supabase_headers(), timeout=10)
        jobs = res.json() if res.ok else []
        return jsonify({'jobs': jobs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500