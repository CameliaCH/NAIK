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

from services.cv_translator_service import translate_to_cv
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
    except FileNotFoundError:
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
        # Only re-fetch if avatar or name might be stale
        # (lightweight: runs on every request, single row lookup)
        try:
            load_session_from_db(uid)
        except Exception:
            pass  # Don't break the page if DB is momentarily unavailable


# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════
@app.route("/recommendations")
def recommendations():
    # Require login to see recommendations
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
    # Already logged in → redirect home
    if session.get("user_id"):
        return redirect(url_for("home"))
    return render_template("signIn.html")

@app.route("/cv-builder")
def cv_builder_page():
    return render_template("cv_builder.html")


# ══════════════════════════════════════════════════════════════
#  PROFILE PAGE
# ══════════════════════════════════════════════════════════════

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("signIn"))
    import json
    # Fetch full user row for the profile page
    res = supabase.table("users").select("*").eq("id", session["user_id"]).single().execute()
    user = res.data or {}
    # Fetch quiz responses
    quiz_res = supabase.table("quiz_responses") \
        .select("*") \
        .eq("user_id", session["user_id"]) \
        .order("created_at", desc=True) \
        .execute()
    quiz_responses = quiz_res.data or []
    # Pass job data so the profile page can show saved jobs
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
    allowed = {"name", "surname", "headline", "description", "age", "gender", "email"}
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
    """
    Receives a file upload, stores it in Supabase Storage bucket 'avatars',
    saves the public URL back to the users table.
    """
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
        # Upsert into Supabase Storage bucket named "avatars"
        supabase.storage.from_("avatars").upload(
            path        = file_path,
            file        = file_bytes,
            file_options= {"content-type": file.content_type, "upsert": "true"},
        )
        # Get public URL
        public_url = supabase.storage.from_("avatars").get_public_url(file_path)

        # Save to DB
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


# ── Save quiz responses ────────────────────────────────────────
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


# ── Professional Me ────────────────────────────────────────────
@app.route("/cv-builder/translate", methods=["POST"])
def cv_translate():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = translate_to_cv(data["text"])
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
