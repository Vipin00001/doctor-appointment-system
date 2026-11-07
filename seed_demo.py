"""Optional: fill the database with demo doctors, a demo patient and sample appointments.

Run:  python seed_demo.py
"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import app, get_db, init_db

DOCTORS = [
    ("Anil Sharma", "anil@clinic.com", "Cardiologist", "MBBS, MD (Cardiology)", 12, 800),
    ("Priya Verma", "priya@clinic.com", "Dermatologist", "MBBS, MD (Dermatology)", 8, 600),
    ("Rohit Gupta", "rohit@clinic.com", "Orthopedic", "MBBS, MS (Ortho)", 15, 700),
    ("Neha Singh", "neha@clinic.com", "Pediatrician", "MBBS, DCH", 6, 500),
]

with app.app_context():
    init_db()
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        for name, email, spec, qual, exp, fee in DOCTORS:
            cur = db.execute(
                "INSERT INTO users (name,email,password_hash,phone,role) VALUES (?,?,?,?, 'doctor')",
                (name, email, generate_password_hash("doctor123"), "9876543210"),
            )
            db.execute(
                "INSERT INTO doctors (user_id,specialization,qualification,experience,fee) VALUES (?,?,?,?,?)",
                (cur.lastrowid, spec, qual, exp, fee),
            )
        cur = db.execute(
            "INSERT INTO users (name,email,password_hash,phone,role) VALUES (?,?,?,?, 'patient')",
            ("Rahul Kumar", "rahul@example.com", generate_password_hash("patient123"), "9123456780"),
        )
        pid = cur.lastrowid
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        for doc_id, slot, reason, status in [
            (1, "10:00", "Chest pain checkup", "Approved"),
            (2, "11:00", "Skin allergy", "Pending"),
            (3, "15:00", "Knee pain", "Pending"),
        ]:
            db.execute(
                """INSERT INTO appointments (patient_id,doctor_id,appt_date,time_slot,reason,status)
                   VALUES (?,?,?,?,?,?)""",
                (pid, doc_id, tomorrow, slot, reason, status),
            )
        db.commit()
        print("Demo data added.")
    else:
        print("Database already has doctors; nothing added.")
    print("Admin:   admin@clinic.com / admin123")
    print("Doctor:  anil@clinic.com / doctor123")
    print("Patient: rahul@example.com / patient123")
