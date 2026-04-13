from flask import Flask, request, jsonify, render_template, session, flash, url_for, redirect
from passlib.hash import argon2
from dotenv import load_dotenv
from db import supabase
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

from blueprints.interview import interview_bp
app.register_blueprint(interview_bp, url_prefix='/interview')

from roadmap_backend import roadmap_bp
app.register_blueprint(roadmap_bp)

from services.cv_translator_service import translate_to_cv

@app.route("/")
@app.route("/home")
def home():
    return render_template("NAIK.html")

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/skills")
def skills():
    return render_template("skills.html")

@app.route("/know")
def know():
    return render_template("know.html")

@app.route("/roadmap")
def quiz():
    return render_template("roadmap.html")

@app.route("/saved")
def savedRoadmaps():
    return render_template("saved_roadmaps.html")

@app.route("/jobs")
def jobs():
    return render_template("jobs.html")

@app.route("/CVexamples")
def CVexamples():
    return render_template("CVexamples.html")

@app.route("/jobGuide")
def jobGuide():
    return render_template("jobGuide.html")

@app.route("/donate")
def donate():
    return render_template("donate.html")

@app.route("/signIn")
def signIn():
    return render_template("signIn.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        # Sign in using Supabase Auth
        res = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        # Store the user ID in the Flask session
        session["user_id"] = res.users.id
        flash("Successfully logged in!", "success")
        return redirect(url_for("home"))
        
    except Exception as e:
        flash(f"Login failed: {str(e)}", "danger")
        return redirect(url_for("signIn"))


@app.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.json
    try:
        # Sign in using Supabase Auth
        res = supabase.auth.sign_in_with_password({
            "email": data['email'], 
            "password": data['password']
        })
        
        session["user_id"] = res.user.id 
        return jsonify({"success": True, "redirect": url_for('home')})
        
    except Exception as e:
        # Better error extraction for Supabase
        error_msg = str(e)
        return jsonify({"success": False, "error": error_msg}), 400

@app.route("/auth/signup", methods=["POST"])
def auth_signup():
    data = request.json
    try:
        auth_res = supabase.auth.sign_up({
            "email": data['email'],
            "password": data['password']
        })

        # FIX: Changed .users to .user
        if auth_res.user:
            user_id = auth_res.user.id
            
            profile_data = {
                "id": user_id, 
                "email": data['email'],
                "surname": data.get('surname'),
                "name": data.get('name'),
                "age": data.get('age'),
                "gender": data.get('gender')
            }
            
            supabase.table("users").insert(profile_data).execute()
            return jsonify({"success": True, "message": "Account and profile created!"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/cv-translator")
def cv_translator():
    return render_template("cv_translator.html")

@app.route("/cv-translator/translate", methods=["POST"])
def cv_translate():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    try:
        result = translate_to_cv(data['text'])
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)

# flask --app app run --debug --port 5001