# Import required libraries
from flask import Flask, redirect, request, url_for, session
import requests
import json
import os

# Create a Flask application
app = Flask(__name__)

# Secret key is required to store data inside "session"
app.secret_key = "your_secret_key"


# -------------------------------
# GOOGLE OAUTH CONFIGURATION
# -------------------------------

# Your Google OAuth Client ID (from Google Cloud Console)
GOOGLE_CLIENT_ID = "82002661354-m4c8386bimfd4fn3kls5mm1dodot8rd0.apps.googleusercontent.com"

# Your Google OAuth Client Secret
GOOGLE_CLIENT_SECRET = "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"

# Redirect URL MUST match exactly with the one in Google Cloud → OAuth settings
REDIRECT_URI = "http://localhost:5000/callback"


# -------------------------------
# HOME PAGE
# -------------------------------
@app.route("/")
def home():
    # Simple page with a Google Login button image
    return """
    <h1>Google OAuth Login</h1>
    <p>Click below to sign in using Google:</p>

    <a href='/login'>
        <img src='https://developers.google.com/identity/images/btn_google_signin_dark_normal_web.png'
             alt='Sign in with Google'>
    </a>
    """


# -------------------------------
# STEP 1: SEND USER TO GOOGLE LOGIN
# -------------------------------
@app.route("/login")
def login():

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
# STEP 2: GOOGLE RETURNS AUTH CODE
# -------------------------------
@app.route("/callback")
def callback():

    # Google sends ?code=XXXXXXXX
    code = request.args.get("code")

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

    # Convert response to JSON
    token_json = token_resp.json()

    # Extract access token
    access_token = token_json.get("access_token")



    # ------------------------------------
    # STEP 3: USE TOKEN TO FETCH USER INFO
    # ------------------------------------
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Send GET request with Authorization header
    user_info_resp = requests.get(
        user_info_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Convert user info into JSON
    user = user_info_resp.json()

    # Store user data inside session
    session["user"] = user

    # Redirect user to their profile page
    return redirect(url_for("profile"))


# -------------------------------
# PROTECTED PROFILE PAGE
# -------------------------------
@app.route("/profile")
def profile():
    # If no user is logged in → redirect to login
    if "user" not in session:
        return redirect("/login")

    # Get logged-in user info
    user = session["user"]

    # Render simple HTML showing user name and email
    return f"""
        <h1>Welcome {user.get('name')}</h1>
        <p>Email: {user.get('email')}</p>

        <br><br>
        <a href='/logout'>Logout</a>
    """


# -------------------------------
# LOGOUT ROUTE
# -------------------------------
@app.route("/logout")
def logout():

    # Remove user from session
    session.clear()

    return "Logged out!"


# -------------------------------
# START THE FLASK SERVER
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)
