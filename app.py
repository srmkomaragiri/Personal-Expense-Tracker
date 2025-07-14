# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, session 
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = 'a'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'madhu@2005'  # your password
app.config['MYSQL_DB'] = 'flaskapp_db'  # your database

mysql = MySQL(app)

# HOME PAGE
@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/")
def add():
    return render_template("home.html")

# SIGN UP PAGE
@app.route("/signup")
def signup():
    return render_template("signup.html")

# REGISTER ROUTE (fixed to always return a response)
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM register WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Name must contain only characters and numbers !'
        else:
            cursor.execute('INSERT INTO register VALUES (NULL, %s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            return render_template('signup.html', msg=msg)

    # For GET requests or if validation fails, render signup page with msg
    return render_template('signup.html', msg=msg)

# LOGIN PAGE
@app.route("/signin")
def signin():
    return render_template("login.html")
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM register WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect('/home')
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)

# ADD EXPENSE PAGE
@app.route("/add")
def adding():
    return render_template('add.html')

@app.route('/addexpense', methods=['GET', 'POST'])
def addexpense():
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    paymode = request.form['paymode']
    category = request.form['category']
    
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO expenses VALUES (NULL, %s, %s, %s, %s, %s, %s)', (session['id'], date, expensename, amount, paymode, category))
    mysql.connection.commit()
    
    return redirect("/display")

# DISPLAY EXPENSES
@app.route("/display")
def display():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE userid = %s ORDER BY date DESC', (str(session['id']),))
    expense = cursor.fetchall()
    return render_template('display.html', expense=expense)

# DELETE EXPENSE
@app.route('/delete/<string:id>', methods=['POST', 'GET'])
def delete(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = %s', (id,))
    mysql.connection.commit()
    return redirect("/display")

# EDIT EXPENSE
@app.route('/edit/<id>', methods=['POST', 'GET'])
def edit(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM expenses WHERE id = %s', (id,))
    row = cursor.fetchone()
    return render_template('edit.html', expenses=row)

# UPDATE EXPENSE
@app.route('/update/<id>', methods=['POST'])
def update(id):
    if request.method == 'POST':
        date = request.form['date']
        expensename = request.form['expensename']
        amount = request.form['amount']
        paymode = request.form['paymode']
        category = request.form['category']
        cursor = mysql.connection.cursor()
        cursor.execute(
            "UPDATE expenses SET date = %s, expensename = %s, amount = %s, paymode = %s, category = %s WHERE id = %s",
            (date, expensename, amount, paymode, category, id)
        )
        mysql.connection.commit()
        return redirect("/display")

# LIMIT ROUTES
@app.route("/limit")
def limit():
    return redirect('/limitn')

@app.route("/limitnum", methods=['POST'])
def limitnum():
    if request.method == "POST":
        number = request.form['number']
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO limits VALUES (NULL, %s, %s)', (session['id'], number))
        mysql.connection.commit()
        return redirect('/limitn')

@app.route("/limitn")
def limitn():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT limitss FROM limits ORDER BY id DESC LIMIT 1')
    x = cursor.fetchone()
    s = x[0] if x else 0
    return render_template("limit.html", y=s)

# REPORTS: TODAY, MONTH, YEAR (similar logic)
@app.route("/today")
def today():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT TIME(date), amount FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW())', (str(session['id']),))
    texpense = cursor.fetchall()
    
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND DATE(date) = DATE(NOW()) ORDER BY date DESC', (str(session['id']),))
    expense = cursor.fetchall()
  
    total = t_food = t_entertainment = t_business = t_rent = t_EMI = t_other = 0
    
    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment, t_business=t_business,
                           t_rent=t_rent, t_EMI=t_EMI, t_other=t_other)

@app.route("/month")
def month():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT DATE(date), SUM(amount) FROM expenses WHERE userid= %s AND MONTH(DATE(date))= MONTH(now()) GROUP BY DATE(date) ORDER BY DATE(date)', (str(session['id']),))
    texpense = cursor.fetchall()
    
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND MONTH(DATE(date))= MONTH(now()) ORDER BY date DESC', (str(session['id']),))
    expense = cursor.fetchall()
  
    total = t_food = t_entertainment = t_business = t_rent = t_EMI = t_other = 0
    
    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment, t_business=t_business,
                           t_rent=t_rent, t_EMI=t_EMI, t_other=t_other)

@app.route("/year")
def year():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT MONTH(date), SUM(amount) FROM expenses WHERE userid= %s AND YEAR(DATE(date))= YEAR(now()) GROUP BY MONTH(date) ORDER BY MONTH(date)', (str(session['id']),))
    texpense = cursor.fetchall()
    
    cursor.execute('SELECT * FROM expenses WHERE userid = %s AND YEAR(DATE(date))= YEAR(now()) ORDER BY date DESC', (str(session['id']),))
    expense = cursor.fetchall()
  
    total = t_food = t_entertainment = t_business = t_rent = t_EMI = t_other = 0
    
    for x in expense:
        total += x[4]
        if x[6] == "food":
            t_food += x[4]
        elif x[6] == "entertainment":
            t_entertainment += x[4]
        elif x[6] == "business":
            t_business += x[4]
        elif x[6] == "rent":
            t_rent += x[4]
        elif x[6] == "EMI":
            t_EMI += x[4]
        elif x[6] == "other":
            t_other += x[4]

    return render_template("today.html", texpense=texpense, expense=expense, total=total,
                           t_food=t_food, t_entertainment=t_entertainment, t_business=t_business,
                           t_rent=t_rent, t_EMI=t_EMI, t_other=t_other)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
