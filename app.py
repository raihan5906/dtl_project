# Import required libraries
from flask import Flask, redirect, request, url_for, session, render_template
import requests
import json
import os

# Create a Flask application
app = Flask(__name__)

# Secret key is required to store data inside "session"
app.secret_key = "a4d0cdf210ab9f7adf823b3d998f444fe91e1bb8c57b013d7d3ac120ef98cc77"


# -------------------------------
# GOOGLE OAUTH CONFIGURATION
# -------------------------------
GOOGLE_CLIENT_ID = "82002661354-m4c8386bimfd4fn3kls5mm1dodot8rd0.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

# Must match Google Cloud OAuth redirect setting
REDIRECT_URI = "http://localhost:5000/callback"


# -------------------------------
# DEFAULT ROUTE → Send user to login
# -------------------------------
@app.route("/")
def index():
    return redirect(url_for("home_page"))



# -------------------------------
# HOME PAGE (Newly added)
# -------------------------------
@app.route("/home")
def home_page():
    # Only show home when user is logged in
    if "user" not in session:
        return redirect(url_for("login_form"))

    return render_template("index.html")   # Your new home page



# -------------------------------
# LOGIN PAGE
# -------------------------------
@app.route("/login_form")
def login_form():
    return render_template('login.html')


# Register page
@app.route("/register_form")
def register_form():
    return render_template('register.html')



# -------------------------------
# STEP 1: SEND USER TO GOOGLE LOGIN
# -------------------------------
@app.route("/google_login")
def google_login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code"
        "&client_id=" + GOOGLE_CLIENT_ID +
        "&redirect_uri=" + REDIRECT_URI +
        "&scope=openid%20email%20profile"
        "&access_type=offline"
        "&prompt=consent"
    )
    return redirect(google_auth_url)



# -------------------------------
# STEP 2 & 3: GOOGLE CALLBACK
# -------------------------------
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("login_form"))

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_resp = requests.post(token_url, data=token_data)
    token_json = token_resp.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Failed to get access token", 400

    # Get user info
    user_info_resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user = user_info_resp.json()

    # Save user in session
    session["user"] = user

    # Redirect to profile
    return redirect(url_for("profile_page"))



# -------------------------------
# PROFILE PAGE (Protected)
# -------------------------------
@app.route("/profile_page")
def profile_page():
    if "user" not in session:
        return redirect(url_for("login_form"))

    return render_template('profile.html', user=session["user"])



# -------------------------------
# LOGOUT
# -------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_form"))



# -------------------------------
# RUN SERVER
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
