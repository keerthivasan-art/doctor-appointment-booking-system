# DBMS Viva Preparation

1. **What is a DBMS?** Software that stores, organizes, secures and retrieves data (here: MySQL).
2. **What is a primary key?** A column (set) that uniquely identifies each row and cannot be NULL: `doctor_id`, `appointment_id`.
3. **What is a foreign key?** A column that refers to a primary key in another table: `appointments.doctor_id -> doctors.doctor_id`. It guarantees every appointment points to an existing doctor (referential integrity).
4. **Candidate keys?** Any minimal unique column set. In `doctors` only `doctor_id` is guaranteed unique (names can repeat). In `admins`, both `admin_id` and `username` are candidate keys; `admin_id` is the primary key. In `appointments`, `appointment_id` is the candidate key; (doctor_id, date, time) is unique for active bookings only, enforced through `slot_key`.
5. **Relationship in this project?** One-to-many: one doctor, many appointments.
6. **How is double booking prevented?** A UNIQUE index on the generated column `slot_key` (doctor|date|time, NULL when cancelled). Even two simultaneous requests cannot both insert; the second gets error 1062, which the app turns into "slot just taken".
7. **Why a generated column instead of UNIQUE(doctor_id, date, time)?** A plain unique key would also block rebooking a slot after a cancellation, because cancelled rows stay in the table (we keep history). NULLs are allowed many times in a UNIQUE index, so cancelled rows do not collide.
8. **Why ON DELETE RESTRICT?** To protect appointment history: a doctor with appointments cannot be deleted; admins deactivate instead (`is_active = 0`). CASCADE is also not permitted by MySQL on a column used in a stored generated column.
9. **What is a transaction / ACID?** A group of statements that succeed or fail together. Booking uses `START TRANSACTION`, insert, `COMMIT`, with `ROLLBACK` on error. ACID = Atomicity, Consistency, Isolation, Durability (InnoDB supports it).
10. **Why parameterized queries?** They send user data separately from SQL text, preventing SQL injection. Example: `WHERE appointment_id = %s`.
11. **Normalization?** Organising tables to reduce redundancy. Doctor details live once in `doctors`; appointments store only `doctor_id`. Checked against this schema: all columns are atomic (1NF); each table has a single-column primary key, so there are no partial dependencies (2NF); and no non-key column determines another non-key column (3NF). One assumption: we treat patient name/phone as facts about the booking, because the same email may be used for different patients (for example a parent booking for a child). If you assume email always determines name and phone, a separate `patients` table would be needed to reach 3NF. `slot_key` is a generated column (controlled redundancy used only for the UNIQUE rule).
12. **Why no patients table?** Keeps the mini-project simple; listed as a future enhancement (it would remove repeated patient data and allow patient login).
13. **What are indexes for?** Faster searches: specialization, name, date, status, email, (doctor_id, date).
14. **Which constraints are used?** PRIMARY KEY, FOREIGN KEY, NOT NULL, UNIQUE, CHECK (fee >= 0, phone regex, email pattern), DEFAULT, ENUM.
15. **Logical vs physical delete?** Cancellation sets status = 'Cancelled' (logical), keeping records for history.
16. **How are passwords stored?** Only a salted hash (Werkzeug `generate_password_hash`) in `admins.password_hash`; never plain text.
17. **Is email + ID verification secure authentication?** No; it is a simple academic safeguard. Real systems need accounts, OTP/verification and rate limiting.
18. **What is CSRF?** An attack that makes a logged-in user's browser submit a forged request. Flask-WTF adds a secret token to every state-changing form.
19. **Difference between DELETE, DROP, TRUNCATE?** DELETE removes rows (can filter), TRUNCATE empties a table quickly, DROP removes the table itself.
20. **What is a JOIN? Where used?** Combines rows from tables on a related column; appointment pages join `appointments` with `doctors` to show the doctor name.
