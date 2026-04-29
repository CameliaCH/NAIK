from flask import Flask, request, jsonify, render_template, session, url_for, redirect
from passlib.hash import argon2
from dotenv import load_dotenv
from db import supabase
import os
import json
from functools import lru_cache
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# ─── SESSION LIFETIME ─────────────────────────────────────────
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)


# ─── BLUEPRINTS ───────────────────────────────────────────────
from blueprints.interview import interview_bp
app.register_blueprint(interview_bp, url_prefix='/interview')

from roadmap_backend import roadmap_bp
app.register_blueprint(roadmap_bp)

from services.cv_translator_service import translate_to_cv, translate_caregiving_to_cv
from services.cv_builder_service import build_cv


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def load_session_from_db(user_id: int):
    """Refresh Flask session from the DB row (call after login or on each request)."""
    res = supabase.table("users").select(
        "id, email, name, surname, headline, description, avatar_url, age, gender"
    ).eq("id", user_id).single().execute()
    if not res.data:
        return
    u = res.data
    session.permanent = True
    session["user_id"]    = u["id"]
    session["user_name"]  = f"{u.get('name', '')} {u.get('surname', '')}".strip()
    session["headline"]   = u.get("headline") or "NAIK Member"
    session["avatar_url"] = u.get("avatar_url") or ""


# ── Inject user into every template automatically ─────────────
@app.context_processor
def inject_user():
    return dict(
        current_user_id   = session.get("user_id"),
        current_user_name = session.get("user_name"),
        current_headline  = session.get("headline"),
        current_avatar    = session.get("avatar_url"),
    )


# ─── I18N ─────────────────────────────────────────────────────
_TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), 'translations')
SUPPORTED_LANGS   = {'en', 'ms', 'zh'}

@lru_cache(maxsize=3)
def _load_translations(lang: str) -> dict:
    path = os.path.join(_TRANSLATIONS_DIR, f'{lang}.json')
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _get_nested(d: dict, key: str):
    parts = key.split('.')
    node = d
    for part in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(part)
        if node is None:
            return None
    return node if isinstance(node, str) else None

def _make_translator(lang: str):
    translations = _load_translations(lang)
    en_fallback  = _load_translations('en')
    def t(key: str, fallback: str = '') -> str:
        val = _get_nested(translations, key)
        if val is None:
            val = _get_nested(en_fallback, key)
        return val if val is not None else fallback
    return t

# Keys exposed to JavaScript (only what .js files actually use)
_JS_KEYS = [
    'explore.saveJob', 'explore.savedJob', 'explore.applyNow',
    'explore.toastSaved', 'explore.toastUnsaved',
    'explore.toastSaveFailed', 'explore.toastUnsaveFailed',
    'explore.noSavedJobs', 'explore.heartToSave',
    'explore.signInToSave', 'explore.opportunitiesFound',
    'explore.whyFitLabel', 'explore.whyFitLoading', 'explore.roadmapHint',
    'skills.savedLoading', 'skills.savedViewRoadmap',
    'skills.savedSignIn', 'skills.savedSignInLink',
    'interview.statusStarting', 'interview.statusIdle',
    'interview.statusRecording', 'interview.statusProcessing',
    'interview.statusThinking', 'interview.statusSpeaking',
    'interview.statusStopped', 'interview.micHintIdle',
    'interview.micHintRecording', 'interview.tooShort', 'interview.micDenied',
    'interview.you', 'interview.interviewer',
]

@app.context_processor
def inject_i18n():
    lang = session.get('lang', 'en')
    if lang not in SUPPORTED_LANGS:
        lang = 'en'
    t = _make_translator(lang)
    i18n_js = {k: t(k) for k in _JS_KEYS}
    return dict(t=t, lang=lang, i18n_js=i18n_js)

# ─── LANGUAGE SWITCHER ────────────────────────────────────────
@app.route('/set-lang')
def set_lang():
    lang = request.args.get('lang', 'en')
    if lang not in SUPPORTED_LANGS:
        lang = 'en'
    session['lang'] = lang
    session.modified = True
    referrer = request.referrer
    if referrer:
        ref_host = urlparse(referrer).netloc
        req_host = urlparse(request.url).netloc
        if ref_host == req_host:
            return redirect(referrer)
    return redirect(url_for('home'))


# ── Auto-refresh session data once per request (keep it fresh) ─
@app.before_request
def refresh_session():
    uid = session.get("user_id")
    if uid:
        try:
            load_session_from_db(uid)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/recommendations")
def recommendations():
    if not session.get("user_id"):
        return redirect(url_for('signIn') + '?next=/recommendations')
    return render_template("recommendations.html")


@app.route("/")
@app.route("/home")
def home():
    return render_template("NAIK.html")

@app.route("/logout")
def logout():
    return render_template("logout.html")

@app.route("/interview")
def interview():
    return render_template("interview.html")

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/skills")
def skills():
    return render_template("skills.html")

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/know")
def know():
    return render_template("know.html")

@app.route("/roadmap")
def quiz():
    return render_template("roadmap.html")

@app.route("/saved")
def savedRoadmaps():
    return render_template("saved_roadmaps.html")

@app.route("/roadmap/view")
def roadmap_view():
    if not session.get("user_id"):
        return redirect(url_for("signIn") + "?next=" + request.url)
    return render_template("roadmap_view.html")

@app.route("/jobs")
def jobs():
    return render_template("jobs.html")

@app.route("/CVexamples")
def CVexamples():
    return render_template("CVexamples.html")

@app.route("/jobGuide")
def jobGuide():
    return render_template("jobGuide.html")

@app.route("/signIn")
def signIn():
    if session.get("user_id"):
        return redirect(url_for("home"))
    return render_template("signIn.html")

@app.route("/cv-builder")
def cv_builder_page():
    return render_template("cv_builder.html")

@app.route("/subsidy")
def subsidy():
    return render_template("subsidy.html")

@app.route("/match")
def match():
    return render_template("match.html")

@app.route("/connect")
def connect():
    return render_template("connect.html")


@app.route("/u/<int:user_id>")
def profile_view(user_id):
    if session.get("user_id") == user_id:
        return redirect(url_for("profile"))

    from flask import abort
    try:
        res = supabase.table("users").select(
            "id, name, surname, headline, description, avatar_url, public_saved_jobs, positions"
        ).eq("id", user_id).maybe_single().execute()
        viewed_user = res.data if res else None
    except Exception:
        viewed_user = None

    if not viewed_user:
        abort(404)

    saved_jobs = []

    if viewed_user.get("public_saved_jobs"):
        try:
            sj = supabase.table("saved_jobs").select("job_id").eq("user_id", user_id).execute()
            job_ids = [row["job_id"] for row in (sj.data or [])]
            if job_ids:
                jobs_res = supabase.table("jobs").select("*").in_("id", job_ids).execute()
                jobs_by_id = {str(j["id"]): j for j in (jobs_res.data or [])}
                saved_jobs = [jobs_by_id[str(jid)] for jid in job_ids if str(jid) in jobs_by_id]
        except Exception:
            pass

    import json
    from static.static_data import JOBS
    jobs_json = json.dumps(JOBS)
    return render_template("profile_view.html",
                           viewed_user=viewed_user,
                           saved_jobs=saved_jobs,
                           jobs_json=jobs_json)

# ══════════════════════════════════════════════════════════════
#  PROFILE PAGE
# ══════════════════════════════════════════════════════════════

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("signIn"))
    import json
    res = supabase.table("users").select("*").eq("id", session["user_id"]).single().execute()
    user = res.data or {}
    quiz_res = supabase.table("quiz_responses") \
        .select("*") \
        .eq("user_id", session["user_id"]) \
        .order("created_at", desc=True) \
        .execute()
    quiz_responses = quiz_res.data or []
    from static.static_data import JOBS
    jobs_json = json.dumps(JOBS)
    return render_template("profile.html", user=user, quiz_responses=quiz_responses, jobs_json=jobs_json)


# ══════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/auth/signup", methods=["POST"])
def auth_signup():
    data = request.json
    try:
        check = supabase.table("users").select("email").eq("email", data["email"]).execute()
        if check.data:
            return jsonify({"success": False, "error": "Email already registered"}), 400

        hashed_pw = argon2.hash(data["password"])
        user_data = {
            "email":         data["email"],
            "password_hash": hashed_pw,
            "surname":       data.get("surname"),
            "name":          data.get("name"),
            "age":           data.get("age"),
            "gender":        data.get("gender"),
        }
        supabase.table("users").insert(user_data).execute()
        return jsonify({"success": True, "message": "Account created successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.json
    try:
        res = supabase.table("users").select("*").eq("email", data["email"]).execute()
        if not res.data:
            return jsonify({"success": False, "error": "User not found"}), 404
        user = res.data[0]
        if argon2.verify(data["password"], user["password_hash"]):
            load_session_from_db(user["id"])
            return jsonify({"success": True, "redirect": url_for("home")})
        else:
            return jsonify({"success": False, "error": "Incorrect password"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/auth/logout")
def auth_logout():
    session.clear()
    return redirect(url_for("home"))


# ── Profile update ─────────────────────────────────────────────
@app.route("/auth/profile/update", methods=["POST"])
def profile_update():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.json
    allowed = {"name", "surname", "headline", "description", "age", "gender", "email",
               "public_saved_jobs", "positions"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"success": False, "error": "Nothing to update"}), 400
    try:
        supabase.table("users").update(updates).eq("id", session["user_id"]).execute()
        load_session_from_db(session["user_id"])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ── Avatar upload ──────────────────────────────────────────────
@app.route("/auth/profile/avatar", methods=["POST"])
def profile_avatar():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if "avatar" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file   = request.files["avatar"]
    ext    = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    uid       = session["user_id"]
    file_path = f"avatars/{uid}.{ext}"
    file_bytes = file.read()

    try:
        supabase.storage.from_("avatars").upload(
            path        = file_path,
            file        = file_bytes,
            file_options= {"content-type": file.content_type, "upsert": "true"},
        )
        public_url = supabase.storage.from_("avatars").get_public_url(file_path)
        supabase.table("users").update({"avatar_url": public_url}).eq("id", uid).execute()
        load_session_from_db(uid)
        return jsonify({"success": True, "avatar_url": public_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── Delete account ─────────────────────────────────────────────
@app.route("/auth/delete", methods=["POST"])
def auth_delete():
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Not logged in"}), 401
    try:
        uid = session["user_id"]
        supabase.table("users").delete().eq("id", uid).execute()
        session.clear()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  QUIZ API
# ══════════════════════════════════════════════════════════════

@app.route("/api/quiz/save", methods=["POST"])
def quiz_save():
    """Save quiz answers to DB for logged-in users."""
    data = request.json
    if not data or "answers" not in data:
        return jsonify({"success": False, "error": "No answers provided"}), 400
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    try:
        supabase.table("quiz_responses").upsert({
            "user_id": uid,
            "answers": data["answers"],
        }, on_conflict="user_id").execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/quiz/results", methods=["GET"])
def quiz_results():
    """
    Returns the current user's quiz answers + their saved job IDs.
    Called by explore.html on page load to restore saved state.
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"quiz": None, "savedJobIds": []}), 200

    try:
        # Quiz answers
        qr = supabase.table("quiz_responses") \
            .select("answers") \
            .eq("user_id", uid) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        quiz = qr.data[0]["answers"] if qr.data else None

        # Saved job IDs
        sj = supabase.table("saved_jobs") \
            .select("job_id, saved_at") \
            .eq("user_id", uid) \
            .order("saved_at", desc=False) \
            .execute()
        saved_job_ids = [row["job_id"] for row in (sj.data or [])]

        return jsonify({"quiz": quiz, "savedJobIds": saved_job_ids})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  JOBS API
# ══════════════════════════════════════════════════════════════

@app.route("/api/jobs/all", methods=["GET"])
def jobs_all():
    """Return all jobs from the DB (used by explore.html grid)."""
    try:
        res = supabase.table("jobs").select("*").execute()
        return jsonify({"jobs": res.data or []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/save", methods=["POST"])
def jobs_save():
    """Save a job for the current user."""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.json
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "job_id required"}), 400

    try:
        # upsert so duplicate saves don't error
        supabase.table("saved_jobs").upsert(
            {"user_id": uid, "job_id": job_id},
            on_conflict="user_id,job_id"
        ).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/jobs/unsave", methods=["POST"])
def jobs_unsave():
    """Remove a saved job for the current user."""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.json
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"success": False, "error": "job_id required"}), 400

    try:
        supabase.table("saved_jobs") \
            .delete() \
            .eq("user_id", uid) \
            .eq("job_id", job_id) \
            .execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/jobs/saved", methods=["GET"])
def jobs_saved():
    """
    Return full job objects for all jobs the current user has saved.
    Used by skills.html and profile.html.
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"jobs": []}), 200

    try:
        sj = supabase.table("saved_jobs") \
            .select("job_id, saved_at") \
            .eq("user_id", uid) \
            .order("saved_at", desc=False) \
            .execute()

        job_ids = [row["job_id"] for row in (sj.data or [])]
        if not job_ids:
            return jsonify({"jobs": []})

        # Fetch each job — Supabase `in_` filter
        jobs_res = supabase.table("jobs") \
            .select("*") \
            .in_("id", job_ids) \
            .execute()

        # Return in save-order
        jobs_by_id = {str(j["id"]): j for j in (jobs_res.data or [])}
        ordered = [jobs_by_id[str(jid)] for jid in job_ids if str(jid) in jobs_by_id]
        return jsonify({"jobs": ordered})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs/why-fit", methods=["POST"])
def jobs_why_fit():
    """
    Generate a personalised 'why this job fits you' explanation.
    Requires the user to have quiz results saved.
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"whyFitPersonalised": "", "whyFitTags": []}), 200

    data = request.json or {}
    job_id = data.get("job_id")
    lang   = data.get("lang", "en")

    try:
        # Get quiz answers
        qr = supabase.table("quiz_responses") \
            .select("answers") \
            .eq("user_id", uid) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        if not qr.data:
            return jsonify({"whyFitPersonalised": "", "whyFitTags": []})

        quiz = qr.data[0]["answers"]

        # Get job info
        jr = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if not jr.data:
            return jsonify({"whyFitPersonalised": "", "whyFitTags": []})

        job = jr.data

        # Build a simple rule-based "why fit" response
        # (replace with an actual LLM call if you have one wired up)
        tags = []
        personalised = ""

        # Check quiz flags
        if quiz.get("q_people") is not None and int(quiz["q_people"]) >= 3:
            if job.get("work_type") in ["full-time", "part-time"]:
                tags.append("People-facing role")
        if quiz.get("q_flexible") is not None and int(quiz["q_flexible"]) >= 3:
            if job.get("work_type") in ["part-time", "freelance", "remote"]:
                tags.append("Fits flexible schedule")
        if quiz.get("q_creative") is not None and int(quiz["q_creative"]) >= 3:
            cat = (job.get("category") or "").lower()
            if any(k in cat for k in ["creative", "design", "digital", "media"]):
                tags.append("Matches creative interest")
        if job.get("location_type") == "remote":
            tags.append("Work from home option")
        if job.get("entry_salary_min") and job.get("entry_salary_min") <= 2000:
            tags.append("Low barrier to entry")
        if job.get("work_type") == "freelance":
            tags.append("Set your own hours")

        if tags:
            personalised = f"Based on your answers, this role suits you because it offers {tags[0].lower()}."

        return jsonify({"whyFitPersonalised": personalised, "whyFitTags": tags[:4]})

    except Exception as e:
        return jsonify({"whyFitPersonalised": "", "whyFitTags": [], "error": str(e)}), 200


# ══════════════════════════════════════════════════════════════
#  RECOMMENDATIONS API
# ══════════════════════════════════════════════════════════════

@app.route("/api/recommendations", methods=["POST"])
def api_recommendations():
    """
    Return top 3 job recommendations based on the user's quiz profile.
    Falls back to 3 general jobs if no quiz data exists.
    """
    uid = session.get("user_id")
    if not uid:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json or {}
    lang = data.get("lang", "en")

    try:
        # Fetch quiz data
        qr = supabase.table("quiz_responses") \
            .select("answers") \
            .eq("user_id", uid) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not qr.data:
            return jsonify({"error": "No quiz results found. Please take the career quiz first."}), 404

        quiz = qr.data[0]["answers"]

        # Fetch all jobs
        jr = supabase.table("jobs").select("*").execute()
        all_jobs = jr.data or []

        if not all_jobs:
            return jsonify({"error": "No jobs available"}), 404

        # Score each job against quiz answers
        def score_job(job):
            score = 0
            wt = job.get("work_type", "")
            cat = (job.get("category") or "").lower()

            # Flexibility preference
            if quiz.get("q_flexible") is not None:
                fl = int(quiz["q_flexible"])
                if fl >= 3 and wt in ["part-time", "freelance", "remote"]:
                    score += 3
                elif fl <= 1 and wt == "full-time":
                    score += 2

            # People preference
            if quiz.get("q_people") is not None:
                pp = int(quiz["q_people"])
                if pp >= 3 and any(k in cat for k in ["sales", "hospitality", "care", "service"]):
                    score += 2

            # Creative preference
            if quiz.get("q_creative") is not None:
                cr = int(quiz["q_creative"])
                if cr >= 3 and any(k in cat for k in ["creative", "design", "digital", "media"]):
                    score += 3

            # Growth preference
            if quiz.get("q_growth") is not None:
                gr = int(quiz["q_growth"])
                if gr >= 3:
                    score += 1  # slight preference for growth jobs

            # Outdoor preference
            if quiz.get("q_outdoor") is not None:
                od = int(quiz["q_outdoor"])
                if od >= 3 and any(k in cat for k in ["logistics", "trade", "agri", "transport"]):
                    score += 2

            return score

        scored = sorted(all_jobs, key=score_job, reverse=True)
        top3   = scored[:3]

        # Fetch saved job IDs for this user
        sj = supabase.table("saved_jobs") \
            .select("job_id") \
            .eq("user_id", uid) \
            .execute()
        saved_ids = [row["job_id"] for row in (sj.data or [])]

        # Shape the response to match what recommendations.html expects
        result_jobs = []
        for j in top3:
            entry_min = j.get("entry_salary_min", 0) or 0
            entry_max = j.get("entry_salary_max", 0) or 0
            target_min = j.get("target_salary_min", 0) or 0
            target_max = j.get("target_salary_max", 0) or 0

            result_jobs.append({
                "id":          j.get("id"),
                "emoji":       j.get("emoji", "💼"),
                "title":       j.get("title_en") or j.get("title_bm") or "Job",
                "tagline":     j.get("tagline_en") or "",
                "description": j.get("duties_en") or j.get("description_en") or "",
                "entrySalary": f"RM {entry_min:,}–{entry_max:,}/mo" if entry_min else "See listing",
                "targetSalary":f"RM {target_min:,}–{target_max:,}/mo" if target_min else "See listing",
                "timeline":    j.get("timeline") or "3–6 months",
                "safetyRating":j.get("safety_rating") or "Steady Growth",
                "work_type":   j.get("work_type") or "full-time",
                "location_type": j.get("location_type") or "",
                "category":    j.get("category") or "",
                # Why-fit tags (simple rule-based)
                "whyFitTags":  [],
                "whyFitPersonalised": "",
            })

        return jsonify({"jobs": result_jobs, "savedJobIds": saved_ids})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  CV TRANSLATOR
# ══════════════════════════════════════════════════════════════

@app.route("/cv-builder/translate", methods=["POST"])
@app.route("/cv-translator/translate", methods=["POST"])  # legacy alias
def cv_translate():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = translate_to_cv(data["text"], lang=data.get("lang", "en"))
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cv-builder/translate-caregiving", methods=["POST"])
def cv_translate_caregiving():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = translate_caregiving_to_cv(data["text"], lang=data.get("lang", "en"))
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/professional-me/build", methods=["POST"])
def cv_build():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    try:
        result = build_cv(data)
        return jsonify({"cv": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)

# flask --app app run --debug --port 5001

# ══════════════════════════════════════════════════════════════
#  MENTOR REQUESTS API
# ══════════════════════════════════════════════════════════════

@app.route("/api/mentor/request", methods=["POST"])
def mentor_request_create():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.json or {}
    required = {"mentor_name", "mentor_contact", "topic"}
    if not required.issubset(data):
        return jsonify({"success": False, "error": "Missing fields"}), 400
    try:
        supabase.table("mentor_requests").insert({
            "user_id":        uid,
            "mentor_name":    data["mentor_name"],
            "mentor_contact": data["mentor_contact"],
            "topic":          data["topic"],
            "message":        data.get("message", ""),
            "status":         "pending",
        }).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/mentor/requests", methods=["GET"])
def mentor_requests_list():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"requests": []}), 200
    try:
        res = supabase.table("mentor_requests") \
            .select("*") \
            .eq("user_id", uid) \
            .order("created_at", desc=True) \
            .execute()
        return jsonify({"requests": res.data or []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  CONNECT / COMMUNITY API
# ══════════════════════════════════════════════════════════════

def _author_from_user(user):
    full_name = f"{user.get('name', '')} {user.get('surname', '')}".strip() or "Community Member"
    return {
        "name":       full_name,
        "initial":    (full_name[0] if full_name else "C").upper(),
        "role":       user.get("headline") or "NAIK Member",
        "avatar_url": user.get("avatar_url") or None,
        "url":        f"/u/{user['id']}" if user.get("id") else "#",
    }


@app.route("/api/connect/posts", methods=["GET"])
def connect_posts_list():
    uid = session.get("user_id")
    try:
        res = supabase.table("community_posts") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(50) \
            .execute()
        posts = res.data or []

        if not posts:
            return jsonify({"posts": [], "likedIds": []})

        # Fetch author info in one query
        user_ids = list({p["user_id"] for p in posts})
        users_res = supabase.table("users") \
            .select("id, name, surname, headline, avatar_url") \
            .in_("id", user_ids) \
            .execute()
        users_by_id = {u["id"]: u for u in (users_res.data or [])}

        # Current user's liked post IDs
        liked_ids = set()
        if uid:
            lr = supabase.table("community_likes").select("post_id").eq("user_id", uid).execute()
            liked_ids = {row["post_id"] for row in (lr.data or [])}

        # Reply counts in one query
        post_ids = [p["id"] for p in posts]
        reply_counts = {}
        rc = supabase.table("community_replies").select("post_id").in_("post_id", post_ids).execute()
        for row in (rc.data or []):
            reply_counts[row["post_id"]] = reply_counts.get(row["post_id"], 0) + 1

        shaped = []
        for p in posts:
            user = users_by_id.get(p["user_id"]) or {}
            shaped.append({
                "id":          p["id"],
                "author":      _author_from_user(user),
                "content":     p["content"],
                "image":       p.get("image_url"),
                "tags":        p.get("tags") or [],
                "timestamp":   p["created_at"],
                "likes":       p.get("likes_count", 0),
                "liked":       p["id"] in liked_ids,
                "reply_count": reply_counts.get(p["id"], 0),
            })

        return jsonify({"posts": shaped, "likedIds": list(liked_ids)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/connect/posts", methods=["POST"])
def connect_posts_create():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Sign in to post"}), 401
    data = request.json or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "Content required"}), 400
    try:
        res = supabase.table("community_posts").insert({
            "user_id":   uid,
            "content":   content,
            "image_url": data.get("image_url") or None,
            "tags":      data.get("tags") or [],
        }).execute()
        post = res.data[0] if res.data else {}
        return jsonify({"success": True, "post_id": post.get("id")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connect/posts/<int:post_id>/like", methods=["POST"])
def connect_posts_like(post_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Sign in to like"}), 401
    try:
        existing = supabase.table("community_likes") \
            .select("post_id").eq("post_id", post_id).eq("user_id", uid).execute()
        post_res = supabase.table("community_posts") \
            .select("likes_count").eq("id", post_id).single().execute()
        current = (post_res.data or {}).get("likes_count", 0)

        if existing.data:
            supabase.table("community_likes").delete().eq("post_id", post_id).eq("user_id", uid).execute()
            new_count = max(0, current - 1)
            liked = False
        else:
            supabase.table("community_likes").insert({"post_id": post_id, "user_id": uid}).execute()
            new_count = current + 1
            liked = True

        supabase.table("community_posts").update({"likes_count": new_count}).eq("id", post_id).execute()
        return jsonify({"success": True, "liked": liked, "likes": new_count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connect/posts/<int:post_id>/replies", methods=["GET"])
def connect_posts_replies_list(post_id):
    try:
        res = supabase.table("community_replies") \
            .select("*") \
            .eq("post_id", post_id) \
            .order("created_at", desc=False) \
            .execute()
        replies = res.data or []

        if not replies:
            return jsonify({"replies": []})

        user_ids = list({r["user_id"] for r in replies})
        users_res = supabase.table("users") \
            .select("id, name, surname, headline, avatar_url") \
            .in_("id", user_ids) \
            .execute()
        users_by_id = {u["id"]: u for u in (users_res.data or [])}

        shaped = []
        for r in replies:
            user = users_by_id.get(r["user_id"]) or {}
            shaped.append({
                "id":        r["id"],
                "author":    _author_from_user(user),
                "content":   r["content"],
                "timestamp": r["created_at"],
            })
        return jsonify({"replies": shaped})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/connect/posts/<int:post_id>/replies", methods=["POST"])
def connect_posts_replies_create(post_id):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Sign in to reply"}), 401
    data = request.json or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": "Reply content required"}), 400
    try:
        res = supabase.table("community_replies").insert({
            "post_id": post_id,
            "user_id": uid,
            "content": content,
        }).execute()
        reply = res.data[0] if res.data else {}
        return jsonify({"success": True, "reply_id": reply.get("id")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/connect/image", methods=["POST"])
def connect_upload_image():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"success": False, "error": "Sign in to upload images"}), 401
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    file = request.files["image"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp", "gif"}:
        return jsonify({"success": False, "error": "Invalid file type"}), 400
    import uuid
    file_name = f"posts/{uid}_{uuid.uuid4().hex[:8]}.{ext}"
    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"success": False, "error": "Image too large (max 5 MB)"}), 400
    try:
        supabase.storage.from_("post-images").upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": file.content_type, "upsert": "true"},
        )
        public_url = supabase.storage.from_("post-images").get_public_url(file_name)
        return jsonify({"success": True, "image_url": public_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# flask --app app run --debug --port 5001