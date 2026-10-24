# Doctor Appointment Booking System (MediBook)

A Database Management Systems (DBMS) AAT mini-project: a Flask + MySQL web application where patients browse doctors, book a time slot, view and cancel their appointment, and administrators manage doctors and appointments.

**Author:** Keerthivasan A - II Year B.E. CSE (Class C), Kalaignar Karunanidhi Institute of Technology (KIT-CBE), Register No. 711525BCS073

> Academic demonstration only. Doctor records are fictional sample data. The app has not had a security assessment and must not be used for real patient data.

## Problem statement
Booking a doctor by phone or in person is slow and error-prone (double bookings, lost records). This project stores doctors and appointments in a relational database and enforces booking rules with SQL constraints.

## Features
- Home page with statistics read from live SQL queries
- Doctor directory with search by name and filter by specialization
- Booking form: client and server validation, free-slot check, unique appointment ID
- Double booking blocked by a database UNIQUE constraint (cancelled slots can be re-booked)
- Confirmation page (shown only after the transaction commits)
- Appointment lookup by ID + booking email, with cancellation (history is kept)
- Admin area (login required): manage doctors, activate/deactivate, view/filter appointments, mark Completed/Cancelled
- Responsive, accessible UI (semantic HTML, focus states, keyboard friendly)

**Design decision (privacy):** appointments are *not* listed publicly. Patients find their own booking with ID + email; the full list with date/status filters is in the admin area.

## Technology stack
HTML5, CSS3, vanilla JavaScript | Python 3, Flask, Flask-WTF (CSRF) | MySQL (mysql-connector-python) | VS Code, MySQL Workbench, Git, GitHub

## Architecture
Browser -> Flask routes (`app/routes.py`, `app/admin.py`) -> validation (`app/services/validation.py`) -> data access (`app/models.py`, parameterized SQL) -> MySQL.

## Database schema summary
| Table | Purpose | Key points |
|-------|---------|-----------|
| doctors | doctor directory | PK doctor_id; CHECK fee >= 0; indexes on name, specialization |
| appointments | bookings | PK appointment_id; FK doctor_id -> doctors (RESTRICT); UNIQUE slot_key; CHECK phone/email; ENUM status |
| admins | admin login | PK admin_id; UNIQUE username; password **hash** only |

![ER diagram](docs/diagrams/er.png)

Full details: `database/schema.sql`, `docs/ER_Diagram.md`, `docs/DFD.md`, `docs/Flowchart.md`.

## Folder structure
```
doctor-appointment-booking-system/
|-- app/ (__init__.py, routes.py, admin.py, models.py, services/, templates/, static/)
|-- database/ (schema.sql, sample_data.sql)
|-- docs/ (ER_Diagram.md, DFD.md, Flowchart.md, Testing_Checklist.md, Viva_Questions.md, diagrams/)
|-- report/ (DBMS_AAT_Report.docx)
|-- screenshots/
|-- tests/ (conftest.py, test_app.py)
|-- .env.example  .gitignore  requirements.txt  config.py  run.py  create_admin.py  LICENSE  README.md
```

## Prerequisites (Windows)
Python 3.10+ (tick "Add Python to PATH"), MySQL Server 8.x + MySQL Workbench, Visual Studio Code, Git.

## Installation (PowerShell, inside the project folder)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

## MySQL setup
1. Start MySQL Workbench and connect to your local server.
2. Open `database/schema.sql` and run it (lightning icon). This creates `doctor_appointment_db`.
3. Open `database/sample_data.sql` and run it (inserts 8 sample doctors).

## Environment configuration
```powershell
copy .env.example .env
```
Edit `.env`: set `DB_USER`, `DB_PASSWORD`, and a long random `SECRET_KEY` (for example: `python -c "import secrets; print(secrets.token_hex(32))"`). Never commit `.env`.

Create the first administrator (password is typed hidden, stored hashed):
```powershell
python create_admin.py
```

## Run the application
```powershell
python run.py
```
Open http://127.0.0.1:5000 . Admin login: http://127.0.0.1:5000/admin/login

## Run the tests
```powershell
python -m pytest -v
```
The tests create and drop a separate database (`doctor_appointment_test`) using the credentials in `.env`, so that MySQL user needs CREATE/DROP rights. Test results must be generated on your own machine; see `docs/Testing_Checklist.md`.

## Screenshots
Real screenshots captured from the running application are in `screenshots/` (home, doctors, booking, confirmation, lookup, cancellation, admin, mobile).

## Troubleshooting
| Problem | Fix |
|---------|-----|
| `Access denied for user` | Wrong `DB_USER`/`DB_PASSWORD` in `.env`. Test the same login in Workbench. |
| `Unknown database 'doctor_appointment_db'` | Run `database/schema.sql` first. |
| `ModuleNotFoundError` | Activate the venv, then `pip install -r requirements.txt`. |
| Port 5000 already in use | Change the port in `run.py`, or close the other program. |
| `Can't connect to MySQL server` | Start the MySQL service (Windows: Services -> MySQL80 -> Start). |
| `SECRET_KEY is not set` | Create `.env` from `.env.example` and set `SECRET_KEY`. |
| "Slot just taken" | Another active booking has that doctor/date/time. Choose another slot. |
| Invalid date/time message | Date must be today or later (within 60 days); choose a slot from the list. |
| `git push` authentication failed | Use a GitHub Personal Access Token as the password, or sign in with Git Credential Manager. |

## Security summary
Implemented: parameterized SQL, server-side validation, CSRF tokens, hashed admin passwords, server-side admin authorization, session cookie flags, safe error pages, transactions, UNIQUE slot constraint.
Not implemented (future): login rate limiting, patient accounts/OTP, HTTPS deployment config, audit logging, email notifications, a formal security review. Email+ID verification for cancellation is **not** real authentication.

## Future enhancements
Patients table and accounts, per-doctor availability schedules, email/SMS reminders, rescheduling, payments, admin audit log, deployment with HTTPS.

## Upload to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Doctor Appointment Booking System"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/doctor-appointment-booking-system.git
git push -u origin main
```
Replace `YOUR-USERNAME` with your real GitHub username and create the empty repository on github.com first. Check `git status` shows no `.env` before committing.

## License
MIT - see `LICENSE`.
