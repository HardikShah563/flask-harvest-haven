from flask import Flask, request, jsonify, session
from flask.templating import render_template
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from database import *
import hashlib
import base64
from flask_cors import CORS

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)
session = {}

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
            return jsonify({"message": "Login Successful", "isAdmin": adminCheck(email)}), 200
        else:
            return jsonify({"error": "Internal Server Error"}), 500
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
            print(session["cart"])
            return jsonify({"message": "success"}), 200
        
        return jsonify({"categories": categories, "items": allItems}), 200
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
    try:
        if request.method == "POST":
            data = request.get_json()
            fullName = data["name"]
            email = data["email"]
            address = data["address"]
            city = data["city"]
            state = data["state"]
            zip = data["zip"]
            total = data["total"]
            msg = checkoutPurchase(session['u_id'], fullName, email, address, city, state, zip, total, session['cart'])
            if(msg) == None:
                session['cart'] = initializeCart()
                return jsonify({"message": "Order Placed Successfully"}), 200
            else: 
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/admin-dashboard', methods=["GET"])
def adminDashboard(): 
    try:
        allItems = getAllItemsFromDB()
        allCategories = getAllCategories()
        return jsonify({"categories": allCategories, "items": allItems}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------
@app.route('/admin-stats', methods=["GET"])
def adminStats():
    try:
        items = getItemsForStats()
        stats = {
            "totalusers" : totalUsers(),
            "male" : totalMaleUsers(),
            "female" : (totalUsers() - totalMaleUsers()),
            "orders"  : totalOrders(),
            "totalsales" : totalSales(),
            "salesRevenue" : totalSalesRevenue(),
            "averageOrderValue" : averageOrderValue(),
            "repeatPurchaseRate" : repeatPurchaseRate(),
            "bestSellingProduct" : bestSellingProducts(),
            "slowMovingProduct" : slowMovingProduct(),
            "stockLevels" : stockLevels(),
        }
        if request.method == "GET":
            return jsonify({"items": items, "stats": stats}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/add-item', methods=["GET", "POST"])
def addItem():
    try:
        allCategories = getAllCategories()
        if request.method == 'GET':
            return jsonify({"categories": allCategories, }), 200
        
        if request.method == 'POST':
            data = request.get_json()
            pName = data['p_name']
            pQty = data['p_qty']
            pPrice = data['p_price']
            pStockQty = data['p_stock_qty']
            pImg = data['p_img']
            cID = data['c_id']

            msg = putItems(pName, pQty, pPrice, pStockQty, pImg, cID)
            if(msg == None):
                getAllItemsFromDB()
                return jsonify({"message": "New Item Created Successfully"}), 200
            else:
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/edit-item', methods=["GET", "POST"])
def editItem():
    try:
        allCategories = getAllCategories()
        allItems = getAllItemNamesAndIDs()
        if request.method == 'GET':
            return jsonify({"items": allItems, "categories": allCategories}), 200

        if request.method == 'POST':
            data = request.get_json()
            p_id = data["p_id"]
            new_name = data["new_name"]
            c_id = data["c_id"]
            p_qty = data["p_qty"]
            p_price = data["p_price"]
            p_stock_qty = data["p_stock_qty"]

            productDetails = getProductFromID(p_id)
            if c_id == None: 
                c_id = productDetails[6]
            
            if p_qty == None:
                p_qty = productDetails[2]

            if p_stock_qty == None:
                p_stock_qty = productDetails[4]
            
            if p_price == None: 
                p_price = productDetails[3]

            msg = editItemDetails(c_id, p_id, new_name, p_qty, p_price, p_stock_qty)
            if(msg == None):
                return jsonify({"message": "Item Edited Successfully"}), 200

            else:
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/delete-item', methods=["GET", "POST"])
def deleteItem():
    try:
        allItems = getAllItemNamesAndIDs()
        if request.method == "GET":
            return jsonify({"items": allItems}), 200
        
        if request.method == "POST": 
            data = request.get_json()
            p_id = data["p_id"]
            msg = deleteProduct(p_id)
            if(msg == None): 
                return jsonify({"message": "Item Deleted Successfully"}), 200

            else: 
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/add-category', methods=["GET", "POST"])
def addCategory():
    try:
        if request.method == "POST":
            data = request.get_json()
            c_name = data["c_name"]
            msg = addNewCategory(c_name)    
            if(msg == None): 
                getAllItemsFromDB()
                return jsonify({"message": "New Category Created Successfully"}), 200

            else: 
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/edit-category', methods=["GET", "POST"])
def editCategory():
    try:
        allCategories = getAllCategories()
        if request.method == "GET":
            return jsonify({"categories": allCategories}), 200

        if request.method == "POST":
            data = request.get_json()
            oldID = data["old_name"]
            newName = data["new_name"]
            msg = editCategoryName(oldID, newName)
            if(msg == None): 
                return jsonify({"message": "Category Updated Successfully"}), 200

            else: 
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/delete-category', methods=["GET", "POST"])
def deleteCategory():
    try:
        allCategories = getAllCategories()
        if request.method == "GET":
            return jsonify({"categories": allCategories}), 200

        if request.method == "POST":
            data = request.get_json()
            c_id = data["c_id"]
            msg = deleteCategoryCompletely(c_id)
            if(msg == None): 
                return jsonify({"message": "Category Deleted Successfully"}), 200

            else: 
                return jsonify({"error": "Internal Server Error"}), 500
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

# -------------------------------------------------------

@app.route('/success')
def success():
    return jsonify({"title": "Your Order Has Been Placed", "subtitle": "Explore the store"}), 200

# -------------------------------------------------------

@app.route('/not-authorized')
def message():
    return jsonify({"title": "You do not have administrative rights", "subtitle": "You should have authorization to visit this page"}), 200

# -------------------------------------------------------
# function to sign out user, clear the session variables
@app.route('/signout', methods=["GET"])
def signout(): 
    try:
        destroySession()
        initializeSession()
        session['cart'] = initializeCart()
        return jsonify({"message": "Logout Successful"}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Internal Server Error"}), 500

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