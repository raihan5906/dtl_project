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
        "https://accounts.google.com/o/oauth2/v2/auth?" #authorization block
        "response_type=code"
        # Tells Google: "I want an authorization code." This code is a temporary, one-time key that 
        # your server will exchange for the real access key later. This two-step process is what 
        # makes the login secure.
        "&client_id=" + GOOGLE_CLIENT_ID + #Your application's unique ID, which Google uses to 
        #identify your specific app.
        "&redirect_uri=" + REDIRECT_URI + #The URL where Google must send the user's browser after 
        #they successfully log in on the Google side (our /callback route).
        "&scope=openid%20email%20profile" #This is the most important part! It defines exactly 
        # what information you are asking the user for access to: openid (basic ID), 
        # email, and profile (name and picture).
        "&access_type=offline" # Asks Google for a special refresh token later on. This allows your 
        # app to access the user's data (if needed) even when they are not actively using your site.
        "&prompt=consent" # Ensures Google asks the user to explicitly select an account and grant 
        # permission every time, providing a clear consent prompt.
    )
    return redirect(google_auth_url) 
# The final line, return redirect(google_auth_url), is what takes the user away from your 
# application and sends them to the Google sign-in screen with this authorization request attached.



# -------------------------------
# STEP 2 & 3: GOOGLE CALLBACK
# -------------------------------
@app.route("/callback")
def callback():
    code = request.args.get("code")  # after session creation only this code runs
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
    return redirect(url_for("home_page"))

# This part of your code handles the complete Google Login process from start to finish. 
# When a user clicks “Login with Google,” they are sent to the /google_login route, where your 
# app builds a special Google OAuth URL. This URL tells Google who your app is (client_id), 
# where Google should send the user after login (redirect_uri), and what information your app 
# wants (email, profile, etc.). Your code then redirects the user to this Google login page. 
# After the user successfully logs in and gives permission, Google redirects them back to your 
# /callback route and includes a temporary code in the URL. Your callback function takes this 
# code and exchanges it with Google for an access token, which is a secure key that allows your 
# server to request the user’s details. Using this access token, your code calls Google’s 
# userinfo API to get the user’s email, name, and profile photo. This data is saved inside 
# session["user"] so the user stays logged in across pages without logging in again. 
# After saving the user, your app redirects them to the home page. You also have a protected 
# /profile_page route that shows the user’s profile, but only if they are logged in 
# (meaning session["user"] exists). If someone tries to open the profile page without logging 
# in, they are sent back to the login page. Finally, the /logout route clears the session, 
# logging the user out and returning them to the login form. The entire process ends with the 
# Flask server running in debug mode, making development easier.


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
