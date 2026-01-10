from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_mail import Mail, Message
from functools import wraps
from db_config import db
from datetime import datetime, date
import random

# ML
from ai_model import train_and_predict
from ml_model import future_trend

from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "secret123"

# ================= EMAIL CONFIG =================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "yashpalgirase122@gmail.com"
app.config["MAIL_PASSWORD"] = "fxwtlioexwxssfud"   # APP PASSWORD

mail = Mail(app)

# ================= LOGIN REQUIRED =================
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

# ================= CUSTOMER HISTORY =================
@app.route("/customer/<path:name>")
@login_required
def customer_history(name):
    cur = db.cursor(dictionary=True)

    # URL decode + clean
    clean_name = name.replace("%20", " ").strip()

    print("Searching history for:", clean_name)  # DEBUG

    cur.execute("""
        SELECT *
        FROM sales
        WHERE TRIM(customer) = %s
        ORDER BY date DESC
    """, (clean_name,))

    history = cur.fetchall()

    return render_template(
        "customer_history.html",
        customer=clean_name,
        history=history
    )

# ================= CUSTOMER SEARCH =================
@app.route("/customer-search", methods=["GET", "POST"])
@login_required
def customer_search():
    name = request.values.get("customer")

    cur = db.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM sales WHERE customer LIKE %s ORDER BY date DESC",
        (f"%{name}%",)
    )
    records = cur.fetchall()

    return render_template(
        "customer_history.html",
        customer=name,
        records=records
    )


# ================= FORGOT PASSWORD =================
@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        otp = random.randint(100000, 999999)

        session["otp"] = str(otp)
        session["email"] = email

        msg = Message(
            "Your OTP",
            sender=app.config["MAIL_USERNAME"],
            recipients=[email]
        )
        msg.body = f"Your OTP is {otp}"
        mail.send(msg)

        return redirect(url_for("otp"))

    return render_template("forgot.html")

# ================= OTP VERIFY =================
@app.route("/otp", methods=["GET", "POST"])
def otp():
    if request.method == "POST":
        entered = request.form.get("otp")

        if str(session.get("otp")) == entered:
            return redirect(url_for("reset"))

        flash("Invalid OTP")

    return render_template("otp.html")

# ================= RESET PASSWORD =================
@app.route("/reset", methods=["GET","POST"])
def reset():
    if request.method == "POST":
        new_pass = request.form["password"]
        email = session.get("email")

        cur = db.cursor()
        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new_pass, email)
        )
        db.commit()

        session.clear()
        flash("Password reset successful")
        return redirect(url_for("login"))

    return render_template("reset.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        flash("Invalid login")
    return render_template("login.html")

# ================= SIGNUP =================
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
            (request.form["username"], request.form["email"], request.form["password"])
        )
        db.commit()
        return redirect(url_for("login"))
    return render_template("signup.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= DASHBOARD =================
@app.route("/dashboard")
@login_required
def dashboard():
    cur = db.cursor()
    cur.execute("SELECT SUM(total) FROM sales")
    total_sales = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(profit) FROM sales")
    total_profit = cur.fetchone()[0] or 0

    return render_template(
        "dashboard.html",
        total_sales=total_sales,
        total_profit=total_profit
    )

# ================= ANALYTICS =================
@app.route("/analytics", methods=["GET", "POST"])
@login_required
def analytics():
    cur = db.cursor(dictionary=True)

    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")
    view = request.form.get("view", "daily")  # daily | monthly | yearly

    # ================= BASE QUERY =================
    query = """
        SELECT 
            DATE(date) AS label,
            SUM(total) AS sales,
            SUM(profit) AS profit
        FROM sales
        WHERE 1=1
    """
    params = []

    if from_date and to_date:
        query += " AND date BETWEEN %s AND %s"
        params.extend([from_date, to_date])

    # ================= GROUPING =================
    if view == "monthly":
        query = query.replace("DATE(date)", "DATE_FORMAT(date, '%Y-%m')")
    elif view == "yearly":
        query = query.replace("DATE(date)", "YEAR(date)")

    query += " GROUP BY label ORDER BY label"

    cur.execute(query, params)
    rows = cur.fetchall()

    dates = [str(r["label"]) for r in rows]
    sales = [float(r["sales"] or 0) for r in rows]
    profit = [float(r["profit"] or 0) for r in rows]

    # ================= PRODUCT WISE =================
    cur.execute("""
        SELECT product, SUM(quantity) AS qty
        FROM sales
        GROUP BY product
    """)
    cat_rows = cur.fetchall()

    categories = [r["product"] for r in cat_rows]
    category_sales = [int(r["qty"]) for r in cat_rows]

    return render_template(
        "analytics.html",
        dates=dates,
        sales=sales,
        profit=profit,
        categories=categories,
        category_sales=category_sales,
        view=view
    )


    # ================= PRODUCT WISE =================
    cur.execute("""
        SELECT product, SUM(quantity) as qty
        FROM sales
        GROUP BY product
    """)
    prod = cur.fetchall()

    categories = [p["product"] for p in prod]
    category_sales = [int(p["qty"]) for p in prod]

    return render_template(
        "analytics.html",
        dates=dates,
        sales=sales,
        profit=profit,
        categories=categories,
        category_sales=category_sales,
        from_date=from_date,
        to_date=to_date,
        view=view
    )


# ================= AI PREDICTION =================
from flask import render_template
from decimal import Decimal
import datetime

@app.route("/prediction")
@login_required
def prediction():
    cur = db.cursor(dictionary=True)

    # ================= TOTAL SALES =================
    cur.execute("SELECT SUM(total) as total_sales FROM sales")
    row = cur.fetchone()
    total_sales = float(row["total_sales"] or 0)

    # ================= MONTHLY SALES =================
    cur.execute("""
        SELECT DATE_FORMAT(date,'%Y-%m') as month,
               SUM(total) as sales
        FROM sales
        GROUP BY month
        ORDER BY month
    """)
    rows = cur.fetchall()

    months = [r["month"] for r in rows]
    sales = [float(r["sales"]) for r in rows]

    # ================= FUTURE PREDICTION (AI LOGIC) =================
    growth_rate = 1.10   # 10% growth
    future_months = []
    future_sales = []

    last_value = sales[-1] if sales else total_sales

    for i in range(1, 7):   # Next 6 months
        last_value = last_value * growth_rate
        future_sales.append(round(last_value, 2))

        future_month = (datetime.date.today() + datetime.timedelta(days=30*i)).strftime("%b %Y")
        future_months.append(future_month)

    # ================= PRODUCT-WISE DEMAND =================
    cur.execute("""
        SELECT product, SUM(quantity) as qty
        FROM sales
        GROUP BY product
    """)
    prod_rows = cur.fetchall()

    products = [p["product"] for p in prod_rows]
    demand = [int(p["qty"]) for p in prod_rows]

    return render_template(
        "prediction.html",
        predicted_sales=round(total_sales * 1.10, 2),
        months=future_months,
        trend=future_sales,
        products=products,
        demand=demand
    )


# ================= BILLING =================
@app.route("/billing", methods=["GET","POST"])
def billing():
    cur = db.cursor(dictionary=True)

    if request.method == "POST":
        customer = request.form["customer"]
        product = request.form["product"]
        qty = int(request.form["qty"])
        sell = float(request.form["sell"])
        buy = float(request.form["buy"])
        outstanding = float(request.form.get("outstanding",0))
        d = request.form["date"]

        total = qty * sell
        profit = (sell - buy) * qty

        cur.execute("""
        INSERT INTO sales
        (customer,product,quantity,sell_price,buy_price,total,profit,outstanding_balance,date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(customer,product,qty,sell,buy,total,profit,outstanding,d))
        db.commit()

    cur.execute("SELECT * FROM sales ORDER BY date DESC")
    sales = cur.fetchall()

    return render_template("billing.html", sales=sales, today=date.today())

# ================= BILL PDF =================
@app.route("/print_bill/<int:bill_id>")
@login_required
def print_bill(bill_id):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM sales WHERE id=%s", (bill_id,))
    bill = cur.fetchone()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "SMART CLOTH SHOP BILL", ln=True, align="C")
    pdf.ln(10)

    for k, v in bill.items():
        pdf.cell(200, 8, f"{k.capitalize()} : {v}", ln=True)

    file_name = f"bill_{bill_id}.pdf"
    pdf.output(file_name)

    return send_file(file_name, as_attachment=True)

# ================= ADMIN =================
@app.route("/admin")
@login_required
def admin():
    user_id = session.get("user_id")

    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, username, email FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM sales ORDER BY date DESC")
    sales = cur.fetchall()

    return render_template("admin.html", user=user, sales=sales)
#---------payment update--------------
@app.route("/update-payment/<int:id>/<status>")
@login_required
def update_payment(id, status):
    cur = db.cursor()

    if status == "Paid":
        cur.execute("""
            UPDATE sales
            SET payment_status='Paid',
                paid_amount = total,
                outstanding_balance = 0
            WHERE id=%s
        """, (id,))
    else:
        cur.execute("""
            UPDATE sales
            SET payment_status='Unpaid',
                paid_amount = 0,
                outstanding_balance = total
            WHERE id=%s
        """, (id,))

    db.commit()
    return redirect(request.referrer)

    return redirect(request.referrer)



# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
