# Doctor Appointment Booking System

MCA Final Year Project - a web application where patients book appointments with doctors, doctors approve or reject them, and an admin manages doctors.

**Tech stack:** Python 3, Flask, SQLite, Jinja2 templates, HTML/CSS, Bootstrap 5

## Features
| Role | What they can do |
|------|------------------|
| Patient | Register, log in, search doctors by name/specialization, book a date + time slot, view and cancel appointments |
| Doctor | Log in, see appointment requests, approve / reject / mark completed |
| Admin | Log in, add / remove doctors, see statistics and all appointments |

Extra: password hashing, role-based access, double-booking prevention, past-date check, parameterized SQL (no SQL injection), 14 automated tests.

## Run it on your computer

```bash
# 1. Get the code
git clone https://github.com/<your-username>/doctor-appointment-system.git
cd doctor-appointment-system

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

# 3. Install requirements
pip install -r requirements.txt

# 4. (Optional) add demo doctors, a demo patient and sample appointments
python seed_demo.py

# 5. Start the app
python app.py
```
Open http://127.0.0.1:5000 in your browser.

### Login details
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@clinic.com | admin123 |
| Doctor (after seed_demo.py) | anil@clinic.com | doctor123 |
| Patient (after seed_demo.py) | rahul@example.com | patient123 |

New patients can register from the Register page.

## Run the tests
```bash
pytest -v
```

## Project structure
```
doctor-appointment-system/
|-- app.py              # Flask app: routes, validation, database code
|-- schema.sql          # Database tables (users, doctors, appointments)
|-- seed_demo.py        # Optional demo data
|-- requirements.txt
|-- templates/          # HTML pages (Jinja2)
|-- static/             # Bootstrap CSS + own CSS
|-- tests/test_app.py   # 14 automated test cases
`-- docs/               # Screenshots and diagrams used in the report
```

## Put this project on GitHub (first time)
1. Create a free account at https://github.com and click **New repository**.
2. Name it `doctor-appointment-system`, keep it **empty** (do not tick README / .gitignore), click **Create repository**.
3. In the project folder run:
```bash
git init                      # skip if the folder already has a .git folder
git add .
git commit -m "Initial commit: Doctor Appointment Booking System"
git branch -M main
git remote add origin https://github.com/<your-username>/doctor-appointment-system.git
git push -u origin main
```
GitHub will ask you to sign in (use a Personal Access Token as the password if it asks for one: GitHub > Settings > Developer settings > Personal access tokens).

Later changes: `git add .` -> `git commit -m "what you changed"` -> `git push`.

## Security note
Set a strong `SECRET_KEY` environment variable and change the default admin password before using this anywhere other than a demo.
