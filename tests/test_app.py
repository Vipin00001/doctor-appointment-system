"""Automated test cases. Run with:  pytest -v"""
import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as appmod  # noqa: E402

FUTURE = (date.today() + timedelta(days=2)).isoformat()
PAST = (date.today() - timedelta(days=2)).isoformat()


@pytest.fixture()
def client(tmp_path):
    appmod.app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.db"))
    with appmod.app.app_context():
        appmod.init_db()
    with appmod.app.test_client() as c:
        yield c


def login(c, email, password):
    return c.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def register(c, name="Test Patient", email="p@test.com", password="secret1", phone="9999999999"):
    return c.post("/register", data={"name": name, "email": email, "password": password,
                                     "phone": phone}, follow_redirects=True)


def add_doctor(c, email="d@test.com"):
    login(c, "admin@clinic.com", "admin123")
    r = c.post("/admin/add_doctor", data={
        "name": "Test Doc", "email": email, "password": "doctor1", "phone": "",
        "specialization": "Cardiologist", "qualification": "MBBS", "experience": 5, "fee": 500},
        follow_redirects=True)
    c.get("/logout")
    return r


# TC01-TC04  registration & login
def test_tc01_patient_registration_success(client):
    assert b"Registration successful" in register(client).data


def test_tc02_duplicate_email_rejected(client):
    register(client)
    assert b"already registered" in register(client).data


def test_tc03_login_valid_and_invalid(client):
    register(client)
    assert b"Welcome, Test Patient" in login(client, "p@test.com", "secret1").data
    client.get("/logout")
    assert b"Invalid email or password" in login(client, "p@test.com", "wrong").data


def test_tc04_short_password_rejected(client):
    assert b"password of 6+" in register(client, password="123").data


# TC05-TC06  access control
def test_tc05_dashboard_requires_login(client):
    r = client.get("/patient", follow_redirects=True)
    assert b"Please log in first" in r.data


def test_tc06_patient_cannot_open_admin_page(client):
    register(client)
    login(client, "p@test.com", "secret1")
    assert b"not allowed" in client.get("/admin", follow_redirects=True).data


# TC07  admin adds doctor
def test_tc07_admin_adds_doctor(client):
    assert b"added successfully" in add_doctor(client).data


# TC08-TC12  booking
def book(c, date_=FUTURE, slot="10:00"):
    return c.post("/book/1", data={"appt_date": date_, "time_slot": slot, "reason": "fever"},
                  follow_redirects=True)


def test_tc08_patient_books_appointment(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    r = book(client)
    assert b"Appointment requested" in r.data and b"Pending" in r.data


def test_tc09_past_date_rejected(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    assert b"future date" in book(client, date_=PAST).data


def test_tc10_double_booking_blocked(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    book(client)
    assert b"already booked" in book(client).data


def test_tc11_doctor_approves_appointment(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    book(client)
    client.get("/logout")
    login(client, "d@test.com", "doctor1")
    r = client.post("/appointment/1/approve", follow_redirects=True)
    assert b"marked Approved" in r.data


def test_tc12_patient_cancels_and_slot_reopens(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    book(client)
    assert b"Appointment cancelled" in client.post("/cancel/1", follow_redirects=True).data
    assert b"Appointment requested" in book(client).data


# TC13  search
def test_tc13_search_doctor_by_specialization(client):
    add_doctor(client)
    register(client)
    login(client, "p@test.com", "secret1")
    assert b"Test Doc" in client.get("/doctors?q=Cardio").data
    assert b"No doctors found" in client.get("/doctors?q=Dentist").data


# TC14  SQL injection attempt is treated as plain text
def test_tc14_sql_injection_login_fails(client):
    r = login(client, "' OR 1=1 --", "x")
    assert b"Invalid email or password" in r.data
