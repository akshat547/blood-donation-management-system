from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
from functools import wraps
import csv

app = Flask(__name__)
app.secret_key = "blood_donation_secret"

# ---------------- DB INIT ----------------
def init_db():
    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    # donors table
    c.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age TEXT,
            blood_group TEXT,
            phone TEXT,
            city TEXT
        )
    """)

    # admin table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    # default admin
    c.execute("SELECT * FROM admin")
    if not c.fetchall():
        c.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("akshat", "akki0130")
        )

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN REQUIRED ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("donors.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        admin = c.fetchone()
        conn.close()

        if admin:
            session["admin"] = username
            return redirect(url_for("index"))
        else:
            msg = "Invalid username or password"

    return render_template("login.html", msg=msg)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/")
@login_required
def index():
    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM donors")
    total_donors = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donors WHERE blood_group='A+'")
    a_positive = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donors WHERE blood_group='B+'")
    b_positive = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donors WHERE blood_group='O+'")
    o_positive = c.fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_donors=total_donors,
        a_positive=a_positive,
        b_positive=b_positive,
        o_positive=o_positive
    )

# ---------------- ADD DONOR ----------------
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_donor():
    if request.method == "POST":
        conn = sqlite3.connect("donors.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO donors (name, age, blood_group, phone, city)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["age"],
            request.form["blood_group"],
            request.form["phone"],
            request.form["city"]
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("donors_list"))

    return render_template("add.html")

# ---------------- DONORS LIST + SEARCH ----------------
@app.route("/donors")
@login_required
def donors_list():
    search_group = request.args.get("blood_group")

    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    if search_group:
        c.execute("SELECT * FROM donors WHERE blood_group=?", (search_group,))
    else:
        c.execute("SELECT * FROM donors")

    donors = c.fetchall()
    conn.close()

    return render_template(
        "donors.html",
        donors=donors,
        search_group=search_group
    )

# ---------------- EDIT DONOR ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_donor(id):
    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""
            UPDATE donors
            SET name=?, age=?, blood_group=?, phone=?, city=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["age"],
            request.form["blood_group"],
            request.form["phone"],
            request.form["city"],
            id
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("donors_list"))

    c.execute("SELECT * FROM donors WHERE id=?", (id,))
    donor = c.fetchone()
    conn.close()

    return render_template("edit.html", donor=donor)

# ---------------- DELETE DONOR ----------------
@app.route("/delete/<int:id>")
@login_required
def delete_donor(id):
    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    c.execute("DELETE FROM donors WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("donors_list"))

# ---------------- ABOUT PAGE ----------------
@app.route("/about")
@login_required
def about():
    return render_template("about.html")

# ---------------- EXPORT CSV ----------------
@app.route("/export")
@login_required
def export_csv():
    conn = sqlite3.connect("donors.db")
    c = conn.cursor()

    c.execute("SELECT * FROM donors")
    data = c.fetchall()
    conn.close()

    def generate():
        yield "ID,Name,Age,Blood Group,Phone,City\n"
        for row in data:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=donors.csv"}
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)