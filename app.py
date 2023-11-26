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

@app.route('/shop', methods=["GET", "POST"])
def shop(): 
    try:
        categories = getCategories()
        categoryIDs = getCategoryID()
        allCategories = getAllCategories()
        allItems = getAllItemsFromDB()
        for category in categories: 
            for item in allItems[category]:
                data = base64.b64encode(item[5])
                item[5] = data.decode()
        
        if request.method == "POST": 
            data = request.get_json()

            op = data["op"]
            p_id = data["p_id"]
            updateCart(p_id, op)
        return jsonify({"categories": categories, "items": allItems}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

def updateCart(p_id, action): 
    limit = getProductFromID(p_id)[7]
    for key in session['cart'].keys(): 
        if key == int(p_id): 
            if action == "plus":
                if session['cart'][key] >= limit:
                    session['cart'][key] = limit
                else:
                    session['cart'][key] += 1
            if action == "minus": 
                if session['cart'][key] <= 1: 
                    session['cart'][key] = 0
                else:
                    session['cart'][key] -= 1

# -------------------------------------------------------

@app.route('/cart', methods=["GET", "POST"])
def cart(): 
    try:
        # allItems = getAllItemsFromDB()
        if request.method == "GET":
            display_cart = recalculateDisplayCart(session['cart'])
            return jsonify({"cart": display_cart}), 200
        
        if request.method == "POST":
            data = request.get_json()
            op = data["op"]
            cart_id = data["cart_id"]
            updateCart(cart_id, op)
            display_cart = recalculateDisplayCart(session['cart'])
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/checkout', methods=["GET", "POST"])
def checkout():
    display_cart = recalculateDisplayCart(session['cart'])
    total = []
    total.append(calcTotal(display_cart))
    total.append(calcGST(total[0]))
    total.append(calcGST(total[0]))
    total.append(total[0] + (total[1] * 2))
    createPurchaseJSON(session['cart'])

    if request.method == "GET":
        return jsonify({"display_cart": display_cart, "total": total})

    if request.method == "POST":
        data = request.get_json()
        fullName = data["fullname"]
        email = data["email"]
        address = data["address"]
        city = data["city"]
        state = data["state"]
        zip = data["zip"]

        msg = checkoutPurchase(session['u_id'], fullName, email, address, city, state, zip, total[3], session['cart'])
        if(msg) == None: 
            msgColor = "green"
            msgText = "Checkout Successful!" 
            reduceStock(display_cart)
            session['cart'] = initializeCart()
            display_cart = {}
            return jsonify({"message": "Order Placed Successfully"}), 200
        else: 
            return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------



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