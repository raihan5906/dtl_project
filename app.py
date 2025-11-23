# Import required libraries
from flask import Flask, redirect, request, url_for, session, render_template, jsonify
import requests
import os
from werkzeug.utils import secure_filename

# Create Flask app
app = Flask(__name__)

# Secret key for session
app.secret_key = "a4d0cdf210ab9f7adf823b3d998f444fe91e1bb8c57b013d7d3ac120ef98cc77"


# ---------------------------------------------------
# STATIC UPLOADS FOLDER  (CREATE THIS FOLDER)
# ---------------------------------------------------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    """Check allowed file extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------
# GOOGLE OAUTH CONFIG
# ---------------------------------------------------
GOOGLE_CLIENT_ID = "82002661354-m4c8386bimfd4fn3kls5mm1dodot8rd0.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = "http://localhost:5000/callback"


# ---------------------------------------------------
# DEFAULT → HOME
# ---------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("home_page"))


# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------
@app.route("/home")
def home_page():
    if "user" not in session:
        return redirect(url_for("login_form"))
    return render_template("home.html", user=session["user"])


# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------
@app.route("/login_form")
def login_form():
    return render_template("login.html")


@app.route("/register_form")
def register_form():
    return render_template("register.html")


# ---------------------------------------------------
# STEP 1: GOOGLE LOGIN URL
# ---------------------------------------------------
@app.route("/google_login")
def google_login():
    google_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code"
        "&client_id=" + GOOGLE_CLIENT_ID +
        "&redirect_uri=" + REDIRECT_URI +
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(google_url)


# ---------------------------------------------------
# STEP 2: GOOGLE CALLBACK
# ---------------------------------------------------
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("login_form"))

    # Exchange code for token
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        return "Google Authentication Failed", 400

    # Get Google profile info
    user = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    # Save user in session (default values added)
    session["user"] = {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "picture": user.get("picture", ""),  # Google picture OR blank
        "bio": "",
        "dob": "",
        "gender": "",
        "skills": ""
    }

    return redirect(url_for("home_page"))


# ---------------------------------------------------
# PROFILE PAGE
# ---------------------------------------------------
@app.route("/profile_page")
def profile_page():
    if "user" not in session:
        return redirect(url_for("login_form"))
    return render_template("profile.html", user=session["user"])


# ---------------------------------------------------
# UPLOAD PROFILE PICTURE (Save as file)
# ---------------------------------------------------
@app.route("/upload_profile_picture", methods=["POST"])
def upload_profile_picture():

    if "user" not in session:
        return jsonify(success=False, error="Not logged in"), 401

    if "picture" not in request.files:
        return jsonify(success=False, error="No picture file"), 400

    file = request.files["picture"]

    if file.filename == "":
        return jsonify(success=False, error="Empty filename"), 400

    if file and allowed_file(file.filename):

        # Filename = user email + .jpg
        filename = secure_filename(session["user"]["email"] + ".jpg")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Save image to static/uploads
        file.save(filepath)

        # Save path in session (NOT the image)
        session["user"]["picture"] = "/" + filepath.replace("\\", "/")
        session.modified = True

        return jsonify(success=True, picture=session["user"]["picture"])

    return jsonify(success=False, error="Invalid file type"), 400


# ---------------------------------------------------
# UPDATE PROFILE: TEXT FIELDS ONLY
# ---------------------------------------------------
@app.route("/update_profile", methods=["POST"])
def update_profile():

    if "user" not in session:
        return jsonify(success=False), 401

    data = request.get_json()
    if not data:
        return jsonify(success=False, error="Bad JSON"), 400

    fields = ["name", "email", "bio", "dob", "gender", "skills"]

    for field in fields:
        if field in data:
            session["user"][field] = data[field]

    session.modified = True
    return jsonify(success=True)


# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_form"))


# ---------------------------------------------------
# RUN SERVER
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
