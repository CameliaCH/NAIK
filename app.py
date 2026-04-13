from flask import Flask, render_template, session, redirect, url_for, request
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

from blueprints.interview import interview_bp
app.register_blueprint(interview_bp, url_prefix='/interview')

from roadmap_backend import roadmap_bp
app.register_blueprint(roadmap_bp)

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)

# flask --app app run --debug --port 5001