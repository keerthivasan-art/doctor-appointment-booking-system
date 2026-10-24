# Testing Checklist

## A. Automated tests (pytest)
Command: `python -m pytest -v` (needs a running MySQL server and a filled `.env`; the tests create and drop their own database, `doctor_appointment_test`).

**Status in this delivery:** 23 tests were executed in the development sandbox against **MariaDB 10.11** (a MySQL-compatible server) and all passed. They have **not** yet been run on your Windows machine with MySQL Server - run them once and record your own result below.

| # | Requirement | Test function | Result on your PC |
|---|-------------|---------------|-------------------|
| 1 | Homepage loads | test_homepage_loads | |
| 2 | Doctor list / filters | test_doctor_list_and_filters | |
| 3 | Valid booking | test_valid_booking_and_retrieval | |
| 4 | Missing values rejected | test_missing_fields_rejected, test_invalid_phone_rejected | |
| 5 | Invalid email rejected | test_invalid_email_rejected | |
| 6 | Past date rejected | test_past_date_rejected | |
| 7 | Unknown / inactive doctor | test_unknown_and_inactive_doctor_handled | |
| 8 | Duplicate slot prevented | test_duplicate_slot_prevented, test_database_unique_constraint_blocks_duplicates | |
| 9 | Retrieve appointment | test_valid_booking_and_retrieval | |
| 10 | Cancellation succeeds | test_cancel_succeeds_and_slot_reusable | |
| 11 | Wrong ID/email does not cancel | test_wrong_id_or_email_does_not_cancel | |
| 12 | No double cancellation | test_cannot_cancel_twice | |
| 13 | SQL errors do not leak secrets | test_sql_error_does_not_leak_secrets | |
| 14 | Admin routes protected | test_admin_pages_require_login (+3 admin tests) | |
| - | CSRF enforced | test_csrf_protection_enabled | |
| - | FK blocks deleting doctor with history | test_doctor_with_appointments_cannot_be_deleted | |

## B. Manual tests (tick on your PC)
- [ ] Home page shows doctor/appointment counts that change after a booking
- [ ] Doctors page search by name and specialization filter work
- [ ] "Book Appointment" on a doctor card pre-selects that doctor
- [ ] Booked slot appears as "(booked)" and is disabled for that doctor/date
- [ ] Submitting an empty form shows error messages
- [ ] Successful booking shows confirmation with appointment ID
- [ ] Refreshing the confirmation page does not create a second booking
- [ ] Lookup with correct ID + email shows details
- [ ] Lookup with wrong email shows "No appointment found"
- [ ] Cancel works once; button disappears afterwards
- [ ] Admin login fails with wrong password; succeeds with correct one
- [ ] Admin can add/edit/deactivate a doctor and mark an appointment Completed
- [ ] Layout works at mobile width (about 390 px) and desktop width

During development the full flow (book, slot shown as booked, lookup, cancel, admin login, admin pages) was exercised once with a headless browser (screenshots in `screenshots/`). That is a development check, not a substitute for your own manual testing.
