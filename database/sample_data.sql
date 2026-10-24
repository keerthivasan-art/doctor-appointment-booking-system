-- =====================================================================
-- SAMPLE DATA - fictional doctors created only for demonstration.
-- They do not represent real people.
-- =====================================================================
USE doctor_appointment_db;

INSERT INTO doctors (name, specialization, qualification, consultation_fee, is_active) VALUES
('Dr. Ananya Rao (Sample)',      'Cardiology',       'MBBS, MD (Cardiology)',        800.00, 1),
('Dr. Rohit Menon (Sample)',     'Dermatology',      'MBBS, MD (Dermatology)',       600.00, 1),
('Dr. Priya Nair (Sample)',      'Pediatrics',       'MBBS, DCH',                    500.00, 1),
('Dr. Karthik Subramanian (Sample)', 'Orthopedics',  'MBBS, MS (Orthopaedics)',      700.00, 1),
('Dr. Meera Iyer (Sample)',      'General Medicine', 'MBBS, MD (General Medicine)',  400.00, 1),
('Dr. Arjun Das (Sample)',       'Neurology',        'MBBS, DM (Neurology)',         900.00, 1),
('Dr. Sneha Pillai (Sample)',    'Gynecology',       'MBBS, MS (Obstetrics & Gynaecology)', 650.00, 1),
('Dr. Vikram Shah (Sample)',     'ENT',              'MBBS, MS (ENT)',               550.00, 0);
