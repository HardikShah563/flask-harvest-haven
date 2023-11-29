import psycopg2
import psycopg2.extras
import base64
import json

from email.message import EmailMessage
import ssl
import smtplib

hostname = 'localhost'
database = 'harvesthaven'
username = 'postgres'
pwd = 'Hardikts@563'
port_id = 5432

conn = None
cur = None

conn = psycopg2.connect(
    host = hostname,
    dbname = database,
    user = username,
    password = pwd,
    port = port_id
)

cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

allProductsInTheStore = {}


create_script = '''
    -- USERS TABLE --
    create table if not exists users (
        u_id integer not null, 
        username varchar(100) not null, 
        gender boolean not null, 
        email varchar(100) not null, 
        passcode varchar(200), 
        isAdmin boolean not null default false, 
        PRIMARY KEY (u_id)
    );

    -- CATEGORY TABLE --
    create table if not exists category (
        c_id integer not null, 
        c_name varchar(100) not null, 
        PRIMARY KEY (c_id)
    );

    -- PRODUCTS TABLE --
    create table if not exists products (
        p_id integer not null, 
        p_name varchar(100) not null, 
        p_qty varchar(50) not null, 
        p_price float not null, 
        p_stock_qty integer not null, 
        p_img bytea not null, 
        c_id integer not null, 
        stock_available integer, 
        PRIMARY KEY (p_id), 
        FOREIGN KEY (c_id) REFERENCES category (c_id)
    );

    -- ORDERS TABLE --
    create table if not exists orders (
        o_id integer not null, 
        u_id integer not null, 
        username varchar(100) not null, 
        email varchar(100) not null, 
        addr varchar(200) not null, 
        city varchar(50) not null, 
        state_province_ut varchar(50) not null, 
        zip integer not null, 
        order_total float not null, 
        purchase jsonb not null, 
        total_order_qty integer not null, 
        PRIMARY KEY (o_id), 
        FOREIGN KEY (u_id) REFERENCES users (u_id)
    );

    -- USER_SEQ_NO SEQUENCE --
    create sequence if not exists public.user_seq_no
        increment 1
        start 1
        minvalue 1
        maxvalue 99999
        owned by users.u_id;

    alter sequence public.user_seq_no
        owner to postgres;

    -- CATEGORY_SEQ_NO SEQUENCE --
    create sequence if not exists public.category_seq_no
        increment 1
        start 1
        minvalue 1
        maxvalue 99999
        owned by category.c_id;

    alter sequence public.category_seq_no
        owner to postgres;

    -- PRODUCT_SEQ_NO SEQUENCE --
    create sequence if not exists public.product_seq_no
        increment 1
        start 1
        minvalue 1
        maxvalue 99999
        owned by products.p_id;

    alter sequence public.product_seq_no
        owner to postgres;

    -- ORDER_SEQ_NO SEQUENCE --
    create sequence if not exists public.order_seq_no
        increment 1
        start 1
        minvalue 1
        maxvalue 99999
        owned by booking.booking_id;

    alter sequence public.order_seq_no
        owner to postgres;
'''
# # gender - true is male and false is female
# # card details wont be save therefore did not make columns for that
# cur.execute(create_script)
# conn.commit()

# -------------------------------------------------------

def registerAccount(name, gender, email, password): 
    insert_script = '''
        select email from users where email = %s
    '''
    insert_values = ([email])
    cur.execute(insert_script, insert_values)
    conn.commit()
    if(cur.fetchall()):
        return False

    insert_script = '''
        insert into users (u_id, username, gender, email, passcode) 
        values (NEXTVAL('user_seq_no'), %s, %s, %s, %s)
    '''
    insert_values = (name, gender, email, password)
    cur.execute(insert_script, insert_values)
    if(conn.commit()): 
       return True

# -------------------------------------------------------

def loginAccount(email, password): 
    insert_script = '''
        select passcode from users where email = %s
    '''
    insert_values = ([email])
    cur.execute(insert_script, insert_values)
    conn.commit()
    data = cur.fetchall()
    if(not data):
        return False
    if(data[0][0] == password): 
        return True
    else: 
        return False

# -------------------------------------------------------

def getUID(email): 
    insert_script = '''
        select u_id from users where email = %s
    '''
    insert_values = ([email])
    cur.execute(insert_script, insert_values)
    conn.commit()
    data = cur.fetchone()
    return data[0]

# -------------------------------------------------------

def getName(email): 
    insert_script = '''
        select username from users where email = %s
    '''
    insert_values = ([email])
    cur.execute(insert_script, insert_values)
    conn.commit()
    data = cur.fetchone()
    return data[0]

# -------------------------------------------------------

def adminCheck(email): 
    insert_script = '''
        select isadmin from users where email = %s
    '''
    insert_values = ([email])
    cur.execute(insert_script, insert_values)
    conn.commit()
    data = cur.fetchone()
    return data[0]

# -------------------------------------------------------

def getAllCategories():
    get_script = '''
        select * from category
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    # categories = []
    # for category in data: 
    #     categories.append(category[0])
    return data

# -------------------------------------------------------

def getCategories(): 
    get_script = '''
        select c_name from category
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    categories = []
    for category in data: 
        categories.append(category[0])
    return categories
 
# -------------------------------------------------------

def getCategoryID(): 
    get_script = '''
        select c_id from category
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    categoryIDs = []
    for id in data: 
        categoryIDs.append(id[0])
    return categoryIDs

# -------------------------------------------------------

def getCategoryById(c_id): 
    get_script = '''
        select c_name from category where c_id = %s
    '''
    get_values = ([c_id])
    cur.execute(get_script, get_values)
    conn.commit()
    data = cur.fetchall()
    return data[0]

# -------------------------------------------------------

def getCategoryIdFromName(c_name): 
    get_script = '''
        select c_id from category where c_name = %s
    '''
    get_values = ([c_name])
    cur.execute(get_script, get_values)
    conn.commit()
    data = cur.fetchall()
    return data

# -------------------------------------------------------

def addNewCategory(c_name):
    add_script = '''
        insert into category
        values (NEXTVAL('category_seq_no'), %s)
    '''
    add_values = ([c_name])
    cur.execute(add_script, add_values)
    if (conn.commit()):
        return True

# -------------------------------------------------------

def editCategoryName(old_id, new_name):
    edit_script = '''
        update category
        set c_name = %s
        where c_id = %s
    '''
    edit_values = (new_name, old_id)
    cur.execute(edit_script, edit_values)
    if (conn.commit()):
        return True

# -------------------------------------------------------

def deleteCategoryCompletely(c_id):
    delete_script = '''
        delete from products where c_id = %s;
        delete from category where c_id = %s;
    '''
    delete_values = (c_id, c_id)
    cur.execute(delete_script, delete_values)
    if (conn.commit()): 
        return True

# -------------------------------------------------------

def getItemsForStats():
    get_script = '''
        select p_id, p_name, p_stock_qty from products
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    return data

def getAllItemsFromDB():
    allProductsInTheStore = {}

    categoryList = getCategories()
    for category in categoryList: 
        allProductsInTheStore[category] = []

    get_script = '''
        select * from products
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()

    for product in data: 
        c_name = getCategoryById(product[6])[0]
        allProductsInTheStore[c_name].append(product)

    return allProductsInTheStore

# -------------------------------------------------------

def getAllItems():
    return allProductsInTheStore

# -------------------------------------------------------

def getAllItemNamesAndIDs(): 
    items = []
    get_script = '''
        select p_id, p_name from products
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    return data

# -------------------------------------------------------

def putItems(pName, pQty, pPrice, pStockQty, pImg, cID):     
    insert_script = '''
        insert into products (p_id, p_name, p_qty, p_price, p_stock_qty, p_img, c_id)
        values (NEXTVAL('product_seq_no'), %s, %s, %s, %s, %s, %s)
    '''
    insert_values = (pName, pQty, pPrice, pStockQty, pImg, cID)
    cur.execute(insert_script, insert_values)
    conn.commit()
    get_script = '''
        select * from products where p_name = %s and p_qty = %s
    '''
    get_values = (pName, pQty)
    cur.execute(get_script, get_values)
    if(conn.commit()): 
       return True

# -------------------------------------------------------

def reduceStock(cart):
    for keys in cart:
        get_script = '''
            select stock_available 
            from products 
            where p_id = %s
        '''
        get_values = ([keys[0]])
        cur.execute(get_script, get_values)
        conn.commit()
        data = cur.fetchone()[0]
        data = data - keys[8]
        update_script = '''
            update products
            set stock_available = %s
            where p_id = %s
        '''
        update_values = (data, keys[0])
        cur.execute(update_script, update_values)
        conn.commit()

# -------------------------------------------------------

def getProductFromID(p_id):
    get_script = '''
        select * from products where p_id = %s
    '''
    get_values = ([p_id])
    cur.execute(get_script, get_values)
    conn.commit()
    data = cur.fetchall()[0]
    return data

# -------------------------------------------------------

def editItemDetails(c_id, p_id, new_name, p_qty, p_price, p_stock_qty):
    edit_script = '''
        update products 
        set p_name = %s, p_qty = %s, p_price = %s, p_stock_qty = %s, c_id = %s where p_id = %s
    '''
    edit_values = (new_name, p_qty, p_price, p_stock_qty, c_id, p_id)
    cur.execute(edit_script, edit_values)
    if (conn.commit()):
        return True

# -------------------------------------------------------

def deleteProduct(p_id):
    delete_script = '''
        delete from products where p_id = %s
    '''
    delete_value = ([p_id])
    cur.execute(delete_script, delete_value)
    if conn.commit(): 
        return True

# -------------------------------------------------------

def initializeCart(): 
    cart = {}
    allItems = getAllItemNamesAndIDs()
    for item in allItems: 
        cart[item[0]] = 0
    return cart

# -------------------------------------------------------

def recalculateDisplayCart(cart):
    display_cart = []
    allItems = getAllItemsFromDB()
    for item in allItems:
        for i in allItems[item]:
            if cart[i[0]] > 0: 
                list = i
                list.append(cart[i[0]])
                data = base64.b64encode(i[5])
                i[5] = data.decode()
                display_cart.append(list)
    return display_cart

# -------------------------------------------------------

def createPurchaseJSON(cart):
    purchase = {}
    for item in cart:
        if (cart[item] > 0):
            purchase[item] = cart[item]
    
    return json.dumps(purchase)

# -------------------------------------------------------

def totalOrderCount(cart):
    count = 0
    for item in cart: 
        count += cart[item]
    return count

def checkoutPurchase(u_id, fullName, email, address, city, state, zip, total, cart): 
    purchase = createPurchaseJSON(cart)
    total_order_qty = totalOrderCount(cart)
    insert_script = '''
        insert into orders (o_id, u_id, username, email, addr, city, state_province_ut, zip, order_total, purchase, total_order_qty)
        values (NEXTVAL('order_seq_no'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    insert_values = (u_id, fullName, email, address, city, state, zip, total, purchase, total_order_qty)
    cur.execute(insert_script, insert_values)
    if (conn.commit()):
        return True

# -------------------------------------------------------

def calcTotal(cart): 
    total = 0
    for cart_item in cart: 
        total = total + (cart_item[3] * cart_item[8])
    return total

# -------------------------------------------------------

def calcGST(total):
    return 0.09 * total

# -------------------------------------------------------

def setShopItemsAndCategories():
    getCategories()
    getCategoryID()
    getAllItemsFromDB()
# -------------------------------------------------------

def sendEmail(email, title, message):
    emailSender = 'hardikts@gmail.com'
    emailPassword = 'iughuynszadhvwrl'
    emailReceiver = email

    subject = "Message Sent to Havest Haven"
    body = "Hello, \nGreetings from Harvest Haven!\nThis is an auto generated email that was sent to Harvest Haven" + "\nFrom: " + email + "\nTitle: " + title + "\nMessage: " + message

    em = EmailMessage()
    em['From'] = emailSender
    em['To'] = emailReceiver
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp: 
        smtp.login(emailSender, emailPassword)
        smtp.sendmail(emailSender, emailReceiver, em.as_string())

# -------------------------------------------------------
# -------------------------------------------------------
# COSTOMER DEMOGRAPHICS:
def totalUsers():
    get_script = '''
        select count(distinct u_id)
        from users
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchone()[0]
    if data == None:
        return 0
    else:
        return data

# -------------------------------------------------------

def totalMaleUsers():
    get_script = '''
        select count(distinct u_id)
        from users
        where gender = True
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchone()[0]
    if data == None:
        return 0
    else:
        return data

# -------------------------------------------------------
# -------------------------------------------------------
# SALES AND REVENUE METRICS: 
def totalSales():
    sales = 0
    get_script = '''
        select sum(order_total)
        from orders
    '''
    cur.execute(get_script)
    conn.commit()
    sales = cur.fetchone()[0]
    if sales == None:
        return 0.0
    else:
        return sales

# -------------------------------------------------------

def totalSalesRevenue():
    sales = totalSales()
    if sales == None:
        return 0
    else:
        return 0.2 * sales

# -------------------------------------------------------

def averageOrderValue():
    get_script = '''
        select avg(order_total)
        from orders
    '''
    cur.execute(get_script)
    conn.commit()
    value = cur.fetchone()[0]
    if value == None:
        return 0.0
    else:
        return value

# -------------------------------------------------------

def repeatPurchaseRate():
    get_script = '''
        select count(distinct u_id)
        from orders
    '''
    cur.execute(get_script)
    conn.commit()
    allBuyers = cur.fetchone()[0]
    if allBuyers == 0:
        return 0

    get_script = '''
        select count(*) as repeat_order_count
        from (
            select u_id
            from orders
            group by u_id
            having count(*) > 1
        ) as repeat_orders
    '''
    cur.execute(get_script)
    conn.commit()
    repeatingBuyers = cur.fetchone()[0]
    return int((repeatingBuyers / allBuyers) * 100)
# -------------------------------------------------------
# -------------------------------------------------------
# INVENTORY AND PRODUCT METRICS: 
def stockLevels():
    get_script = '''
        select p_name, stock_available
        from products
    '''
    cur.execute(get_script)
    conn.commit()
    stock = cur.fetchall()
    # returns a list of list
    # print it in the form of table
    return stock

# -------------------------------------------------------

def bestSellingProducts():
    get_script = '''
        select p_id
        from products
        where (p_stock_qty - stock_available) = (
            select max(p_stock_qty - stock_available)
            from products
        )
    '''
    cur.execute(get_script)
    conn.commit()
    p_id = cur.fetchone()[0]
    product = getProductFromID(p_id)
    data = base64.b64encode(product[5])
    product[5] = data.decode()
    return product

# -------------------------------------------------------

def slowMovingProduct():
    get_script = '''
        select p_id
        from products
        where (p_stock_qty - stock_available) = (
            select min(p_stock_qty - stock_available)
            from products
        )
    '''
    cur.execute(get_script)
    conn.commit()
    p_id = cur.fetchone()[0]
    product = getProductFromID(p_id)
    data = base64.b64encode(product[5])
    product[5] = data.decode()
    return product

# -------------------------------------------------------

def totalOrders():
    get_script = '''
        select count(distinct o_id)
        from orders
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchone()[0]
    if data == None:
        return 0
    else:
        return data

# -------------------------------------------------------

# INCOMPLETE FUNCTION
def customerLifeTimeValue(): 
    get_script = '''
        select u_id, order_total 
        from orders
    '''
    cur.execute(get_script)
    conn.commit()
    data = cur.fetchall()
    value = 0
    return value
