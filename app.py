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

from passlib.hash import argon2 # Ensure this is at the top

@app.route("/auth/signup", methods=["POST"])
def auth_signup():
    data = request.json
    try:
        # 1. Check if the email already exists
        check = supabase.table("users").select("email").eq("email", data['email']).execute()
        if check.data:
            return jsonify({"success": False, "error": "Email already registered"}), 400

        # 2. Hash the password before saving
        hashed_pw = argon2.hash(data['password'])

        # 3. Insert the data directly into your 'users' table
        user_data = {
            "email": data['email'],
            "password_hash": hashed_pw,
            "surname": data.get('surname'),
            "name": data.get('name'),
            "age": data.get('age'),
            "gender": data.get('gender')
        }
        
        supabase.table("users").insert(user_data).execute()
        return jsonify({"success": True, "message": "Account created successfully!"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/auth/login", methods=["POST"])
def auth_login():
    data = request.json
    try:
        # 1. Look for the user by email
        res = supabase.table("users").select("*").eq("email", data['email']).execute()
        
        if not res.data:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        user = res.data[0]

        # 2. Verify the password provided matches the hash in the DB
        if argon2.verify(data['password'], user['password_hash']):
            session["user_id"] = user['id'] # Save their database ID
            return jsonify({"success": True, "redirect": url_for('home')})
        else:
            return jsonify({"success": False, "error": "Incorrect password"}), 401
            
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