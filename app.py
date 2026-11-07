"""Doctor Appointment Booking System - Flask + SQLite.

Three roles:
  admin   - adds / removes doctors, sees all appointments
  doctor  - approves / rejects / completes appointments
  patient - registers, searches doctors, books / cancels appointments
"""
import os
import re
import sqlite3
from datetime import date
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-in-production")
app.config["DATABASE"] = os.path.join(BASE_DIR, "clinic.db")

# Fixed one-hour consultation slots
TIME_SLOTS = ["10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------- database
def get_db():
    """One SQLite connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and a default admin account."""
    db = get_db()
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    admin = db.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if admin is None:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            ("Administrator", "admin@clinic.com",
             generate_password_hash("admin123"), "admin"),
        )
    db.commit()


# ---------------------------------------------------------------- helpers
def login_required(role=None):
    """Decorator: user must be logged in (and have the given role)."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You are not allowed to open that page.", "danger")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_doctor_id():
    row = get_db().execute(
        "SELECT id FROM doctors WHERE user_id = ?", (session["user_id"],)
    ).fetchone()
    return row["id"] if row else None


def slot_is_free(doctor_id, appt_date, slot):
    """A slot is taken if a Pending/Approved appointment already uses it."""
    row = get_db().execute(
        """SELECT 1 FROM appointments
           WHERE doctor_id=? AND appt_date=? AND time_slot=?
             AND status IN ('Pending','Approved')""",
        (doctor_id, appt_date, slot),
    ).fetchone()
    return row is None


# ---------------------------------------------------------------- public pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not name or not EMAIL_RE.match(email) or len(password) < 6:
            flash("Enter a name, a valid email and a password of 6+ characters.", "danger")
        elif phone and not re.fullmatch(r"\d{10}", phone):
            flash("Phone number must be 10 digits.", "danger")
        else:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO users (name,email,password_hash,phone,role) VALUES (?,?,?,?, 'patient')",
                    (name, email, generate_password_hash(password), phone),
                )
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("This email is already registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required()
def dashboard():
    """Send each role to its own dashboard."""
    return redirect(url_for(f"{session['role']}_dashboard"))


# ---------------------------------------------------------------- patient
@app.route("/doctors")
@login_required("patient")
def doctors():
    q = request.args.get("q", "").strip()
    sql = """SELECT d.*, u.name FROM doctors d JOIN users u ON u.id = d.user_id"""
    params = ()
    if q:
        sql += " WHERE u.name LIKE ? OR d.specialization LIKE ?"
        params = (f"%{q}%", f"%{q}%")
    rows = get_db().execute(sql + " ORDER BY u.name", params).fetchall()
    return render_template("doctors.html", doctors=rows, q=q)


@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required("patient")
def book(doctor_id):
    db = get_db()
    doctor = db.execute(
        "SELECT d.*, u.name FROM doctors d JOIN users u ON u.id=d.user_id WHERE d.id=?",
        (doctor_id,),
    ).fetchone()
    if doctor is None:
        flash("Doctor not found.", "danger")
        return redirect(url_for("doctors"))

    today = date.today().isoformat()
    if request.method == "POST":
        appt_date = request.form.get("appt_date", "")
        slot = request.form.get("time_slot", "")
        reason = request.form.get("reason", "").strip()

        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", appt_date) or appt_date < today:
            flash("Choose today's date or a future date.", "danger")
        elif slot not in TIME_SLOTS:
            flash("Choose a valid time slot.", "danger")
        elif not slot_is_free(doctor_id, appt_date, slot):
            flash("That slot is already booked. Please pick another one.", "warning")
        else:
            db.execute(
                """INSERT INTO appointments (patient_id, doctor_id, appt_date, time_slot, reason)
                   VALUES (?,?,?,?,?)""",
                (session["user_id"], doctor_id, appt_date, slot, reason),
            )
            db.commit()
            flash("Appointment requested. Wait for the doctor's approval.", "success")
            return redirect(url_for("patient_dashboard"))
    return render_template("book.html", doctor=doctor, slots=TIME_SLOTS, today=today)


@app.route("/patient")
@login_required("patient")
def patient_dashboard():
    rows = get_db().execute(
        """SELECT a.*, u.name AS doctor_name, d.specialization
           FROM appointments a
           JOIN doctors d ON d.id = a.doctor_id
           JOIN users u ON u.id = d.user_id
           WHERE a.patient_id = ?
           ORDER BY a.appt_date DESC, a.time_slot""",
        (session["user_id"],),
    ).fetchall()
    return render_template("patient_dashboard.html", appointments=rows)


@app.route("/cancel/<int:appt_id>", methods=["POST"])
@login_required("patient")
def cancel(appt_id):
    db = get_db()
    cur = db.execute(
        """UPDATE appointments SET status='Cancelled'
           WHERE id=? AND patient_id=? AND status IN ('Pending','Approved')""",
        (appt_id, session["user_id"]),
    )
    db.commit()
    flash("Appointment cancelled." if cur.rowcount else "Cannot cancel this appointment.",
          "info" if cur.rowcount else "danger")
    return redirect(url_for("patient_dashboard"))


# ---------------------------------------------------------------- doctor
@app.route("/doctor")
@login_required("doctor")
def doctor_dashboard():
    rows = get_db().execute(
        """SELECT a.*, u.name AS patient_name, u.phone
           FROM appointments a JOIN users u ON u.id = a.patient_id
           WHERE a.doctor_id = ?
           ORDER BY a.appt_date DESC, a.time_slot""",
        (current_doctor_id(),),
    ).fetchall()
    return render_template("doctor_dashboard.html", appointments=rows)


@app.route("/appointment/<int:appt_id>/<action>", methods=["POST"])
@login_required("doctor")
def update_appointment(appt_id, action):
    new_status = {"approve": "Approved", "reject": "Rejected", "complete": "Completed"}.get(action)
    if new_status is None:
        flash("Unknown action.", "danger")
        return redirect(url_for("doctor_dashboard"))
    db = get_db()
    # doctor can only change his own appointments
    cur = db.execute(
        "UPDATE appointments SET status=? WHERE id=? AND doctor_id=?",
        (new_status, appt_id, current_doctor_id()),
    )
    db.commit()
    flash(f"Appointment marked {new_status}." if cur.rowcount else "Appointment not found.",
          "success" if cur.rowcount else "danger")
    return redirect(url_for("doctor_dashboard"))


# ---------------------------------------------------------------- admin
@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    db = get_db()
    stats = {
        "patients": db.execute("SELECT COUNT(*) FROM users WHERE role='patient'").fetchone()[0],
        "doctors": db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "appointments": db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        "pending": db.execute("SELECT COUNT(*) FROM appointments WHERE status='Pending'").fetchone()[0],
    }
    doctors_ = db.execute(
        """SELECT d.*, u.name, u.email FROM doctors d
           JOIN users u ON u.id = d.user_id ORDER BY u.name"""
    ).fetchall()
    appts = db.execute(
        """SELECT a.*, p.name AS patient_name, du.name AS doctor_name
           FROM appointments a
           JOIN users p ON p.id = a.patient_id
           JOIN doctors d ON d.id = a.doctor_id
           JOIN users du ON du.id = d.user_id
           ORDER BY a.appt_date DESC, a.time_slot LIMIT 50"""
    ).fetchall()
    return render_template("admin_dashboard.html", stats=stats, doctors=doctors_, appointments=appts)


@app.route("/admin/add_doctor", methods=["GET", "POST"])
@login_required("admin")
def add_doctor():
    if request.method == "POST":
        f = request.form
        name, email = f.get("name", "").strip(), f.get("email", "").strip().lower()
        spec, qual = f.get("specialization", "").strip(), f.get("qualification", "").strip()
        password = f.get("password", "")
        try:
            experience, fee = int(f.get("experience", 0)), int(f.get("fee", 0))
        except ValueError:
            experience, fee = -1, -1

        if not (name and spec and qual) or not EMAIL_RE.match(email) or len(password) < 6:
            flash("Fill all fields correctly (password 6+ characters).", "danger")
        elif experience < 0 or fee < 0:
            flash("Experience and fee must be non-negative numbers.", "danger")
        else:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (name,email,password_hash,phone,role) VALUES (?,?,?,?, 'doctor')",
                    (name, email, generate_password_hash(password), f.get("phone", "").strip()),
                )
                db.execute(
                    """INSERT INTO doctors (user_id, specialization, qualification, experience, fee)
                       VALUES (?,?,?,?,?)""",
                    (cur.lastrowid, spec, qual, experience, fee),
                )
                db.commit()
                flash(f"Dr. {name} added successfully.", "success")
                return redirect(url_for("admin_dashboard"))
            except sqlite3.IntegrityError:
                db.rollback()
                flash("A user with this email already exists.", "danger")
    return render_template("add_doctor.html")


@app.route("/admin/delete_doctor/<int:doctor_id>", methods=["POST"])
@login_required("admin")
def delete_doctor(doctor_id):
    db = get_db()
    row = db.execute("SELECT user_id FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    if row:
        # deleting the user cascades to doctors and appointments
        db.execute("DELETE FROM users WHERE id=?", (row["user_id"],))
        db.commit()
        flash("Doctor removed.", "info")
    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------- run
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
