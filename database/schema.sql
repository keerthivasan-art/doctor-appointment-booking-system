-- =====================================================================
-- Doctor Appointment Booking System - MySQL schema
-- Run this whole file in MySQL Workbench (File > Open SQL Script > Run).
-- WARNING: it DROPs and re-creates the three tables below.
-- No passwords or credentials are stored in this file.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS doctor_appointment_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE doctor_appointment_db;

DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS admins;

-- ---------------------------------------------------------------------
-- Table 1: doctors  (the "one" side of the one-to-many relationship)
-- ---------------------------------------------------------------------
CREATE TABLE doctors (
    doctor_id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name             VARCHAR(100)  NOT NULL,
    specialization   VARCHAR(80)   NOT NULL,
    qualification    VARCHAR(120)  NOT NULL,
    consultation_fee DECIMAL(8,2)  NOT NULL,
    is_active        TINYINT(1)    NOT NULL DEFAULT 1,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id),
    CONSTRAINT chk_doctor_fee    CHECK (consultation_fee >= 0),
    CONSTRAINT chk_doctor_active CHECK (is_active IN (0, 1)),
    INDEX idx_doctors_specialization (specialization),
    INDEX idx_doctors_name (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table 2: appointments  (the "many" side)
-- ---------------------------------------------------------------------
CREATE TABLE appointments (
    appointment_id   INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    doctor_id        INT UNSIGNED  NOT NULL,
    patient_name     VARCHAR(100)  NOT NULL,
    patient_email    VARCHAR(120)  NOT NULL,
    patient_phone    VARCHAR(10)   NOT NULL,
    appointment_date DATE          NOT NULL,
    appointment_time TIME          NOT NULL,
    reason           VARCHAR(500)  NOT NULL,
    status           ENUM('Booked','Completed','Cancelled') NOT NULL DEFAULT 'Booked',
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- slot_key is NULL for cancelled appointments, so a cancelled slot can be
    -- booked again, while two ACTIVE bookings for the same doctor/date/time
    -- collide on the UNIQUE index below (MySQL allows many NULLs in a UNIQUE key).
    slot_key VARCHAR(40) GENERATED ALWAYS AS (
        CASE WHEN status = 'Cancelled' THEN NULL
             ELSE CONCAT(doctor_id, '|', appointment_date, '|', appointment_time) END
    ) STORED,

    PRIMARY KEY (appointment_id),
    UNIQUE KEY uq_active_slot (slot_key),

    -- RESTRICT (not CASCADE): doctor_id feeds a stored generated column, and MySQL
    -- does not allow CASCADE actions on such a column. RESTRICT also protects the
    -- appointment history: a doctor with appointments cannot be deleted
    -- (use is_active = 0 to deactivate instead).
    CONSTRAINT fk_appointments_doctor FOREIGN KEY (doctor_id)
        REFERENCES doctors (doctor_id) ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT chk_phone  CHECK (patient_phone REGEXP '^[6-9][0-9]{9}$'),
    CONSTRAINT chk_email  CHECK (patient_email LIKE '%_@_%._%'),

    INDEX idx_appt_date (appointment_date),
    INDEX idx_appt_status (status),
    INDEX idx_appt_email (patient_email),
    INDEX idx_appt_doctor_date (doctor_id, appointment_date)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table 3: admins  (administrator login; only a password HASH is stored)
-- Create the first admin with:  python create_admin.py
-- ---------------------------------------------------------------------
CREATE TABLE admins (
    admin_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (admin_id),
    UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB;
