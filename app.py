from flask import Flask, request, jsonify, session
from flask.templating import render_template
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from database import *
import hashlib
import base64

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route('/')
def home():
    return "Hello world"

@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()

        if 'email' not in data or 'passcode' not in data:
            return jsonify({"error": "Username and password are required"}), 400

        email = data['email']
        passcode = hashlib.sha256(data['passcode'].encode('utf-8')).hexdigest()
        # calling loginAccount method to check in account exists
        loginExists = loginAccount(email, passcode)
        if(loginExists):
            setSession(getUID(email), getName(email), email, adminCheck(email))
            return jsonify({"message": "Login Successful"}), 200
        else:
            return jsonify({"error": "Internal Server Error"}), 500
        
        # if session['u_id']: 
        #     return redirect("/store")
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        name = data['name']
        email = data['email']
        password = hashlib.sha256(data['passcode'].encode('utf-8')).hexdigest()
        if data['gender'] == "Male": 
            gender = True
        else: 
            gender = False
        
        # calling registerAccount method to create new account
        register = registerAccount(name, gender, email, password)
        if(register == None): 
            return jsonify({"message": "Account Created Successful"}), 200

        else: 
            return jsonify({"error": "Account Already Exists"}), 500
        
        setSession(getUID(email), name, email, adminCheck(email))
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------
# function to sign out user, clear the session variables
@app.route('/signout')
def signout(): 
    destroySession()
    initializeSession()
    session['cart'] = initializeCart()

# -------------------------------------------------------
# function for initializing the session variables
def initializeSession():
    session['u_id'] = 0
    session['username'] = ""
    session['email'] = ""
    session['isAdmin'] = False

# -------------------------------------------------------
# function for setting the session variables
def setSession(u_id, name, email, isAdmin): 
    session['u_id'] = u_id
    session['username'] = name
    session['email'] = email
    session['isAdmin'] = isAdmin
    session['cart'] = initializeCart()

# -------------------------------------------------------
# function for destroying the session variables
def destroySession(): 
    session["u_id"] = None
    session["name"] = None
    session["email"] = None
    session["isAdmin"] = None
    session["cart"] = {}

# -------------------------------------------------------

if __name__ == '__main__': 
    app.run(debug = True)