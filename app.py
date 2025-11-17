# Import required libraries
from flask import Flask, redirect, request, url_for, session, render_template # Changed from render_template_string
import requests
import json
import os

# Create a Flask application
app = Flask(__name__)

# Secret key is required to store data inside "session"
# IMPORTANT: Change this to a secure, random string for production
app.secret_key = "a4d0cdf210ab9f7adf823b3d998f444fe91e1bb8c57b013d7d3ac120ef98cc77"
#nice

# -------------------------------
# GOOGLE OAUTH CONFIGURATION
# -------------------------------

# Your Google OAuth Client ID (from Google Cloud Console)
# I'm keeping your provided placeholder ID, but ensure it is correct
GOOGLE_CLIENT_ID = "82002661354-m4c8386bimfd4fn3kls5mm1dodot8rd0.apps.googleusercontent.com"

# Your Google OAuth Client Secret
# I'm keeping your provided placeholder Secret
GOOGLE_CLIENT_SECRET = "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"

# Redirect URL MUST match exactly with the one in Google Cloud → OAuth settings
REDIRECT_URI = "http://localhost:5000/callback"


# -------------------------------
# LOGIN PAGE ROUTE (Serves login.html)
# -------------------------------
# Note: Ensure login.html, register.html, and profile.html are in a 'templates' folder
@app.route("/")
def index():
    # Redirect to the main login form page
    return redirect(url_for("login_form"))

@app.route("/login_form")
def login_form():
    # Using render_template for standard Flask templating
    return render_template('login.html') 

# Route for the register page
@app.route("/register_form")
def register_form():
    # Using render_template for standard Flask templating
    return render_template('register.html')


# -------------------------------
# STEP 1: SEND USER TO GOOGLE LOGIN
# -------------------------------
@app.route("/google_login")
def google_login():

    # Google authorization URL with required parameters
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code"                 # We want an authorization code
        "&client_id=" + GOOGLE_CLIENT_ID +   # Your client ID
        "&redirect_uri=" + REDIRECT_URI +    # Redirect URL after login
        "&scope=openid%20email%20profile"    # Info we want from user
        "&access_type=offline"               # Allows refresh token
        "&prompt=consent"                    # Always ask user to choose account
    )

    # Redirect browser to Google login page
    return redirect(google_auth_url)


# -------------------------------
# STEP 2 & 3: GOOGLE CALLBACK & PROFILE
# -------------------------------
@app.route("/callback")
def callback():

    # Google sends ?code=XXXXXXXX
    code = request.args.get("code")
    if not code:
        # Handle error if code is missing (e.g., user denied consent)
        return redirect(url_for("login_form"))

    # URL to exchange the auth code for an access token
    token_url = "https://oauth2.googleapis.com/token"

    # Data required to get access token
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    # Send POST request to Google to get access token
    token_resp = requests.post(token_url, data=token_data)
    token_json = token_resp.json()
    access_token = token_json.get("access_token")

    if not access_token:
        # Handle error if token exchange failed
        return "Failed to get access token", 400


    # USE TOKEN TO FETCH USER INFO
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Send GET request with Authorization header
    user_info_resp = requests.get(
        user_info_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user = user_info_resp.json()

    # Store user data inside session
    session["user"] = user

    # Redirect user to their profile page
    return redirect(url_for("profile_page"))


# -------------------------------
# PROTECTED PROFILE PAGE
# -------------------------------
@app.route("/profile_page")
def profile_page():
    # If no user is logged in → redirect to login
    if "user" not in session:
        return redirect(url_for("login_form"))

    # Get logged-in user info
    user = session["user"]

    # Use render_template to load the separate profile.html file
    return render_template('profile.html', user=user)


# -------------------------------
# LOGOUT ROUTE
# -------------------------------
@app.route("/logout")
def logout():

    # Remove user from session
    session.clear()

    # Redirect to the main login page
    return redirect(url_for("login_form"))


# -------------------------------
# START THE FLASK SERVER
# -------------------------------
if __name__ == "__main__":
    # Ensure you are running on http://localhost:5000 for the OAuth to work with your REDIRECT_URI
    app.run(debug=True)