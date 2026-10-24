# ER Diagram

Image: `docs/diagrams/er.png` (generated from `docs/diagrams/er.dot` with Graphviz).

![ER diagram](diagrams/er.png)

Editable Mermaid source (renders automatically on GitHub). It matches `database/schema.sql`.

```mermaid
erDiagram
    DOCTORS ||--o{ APPOINTMENTS : "receives"
    DOCTORS {
        INT_UNSIGNED doctor_id PK
        VARCHAR100 name
        VARCHAR80 specialization
        VARCHAR120 qualification
        DECIMAL consultation_fee
        TINYINT is_active
        TIMESTAMP created_at
    }
    APPOINTMENTS {
        INT_UNSIGNED appointment_id PK
        INT_UNSIGNED doctor_id FK
        VARCHAR100 patient_name
        VARCHAR120 patient_email
        VARCHAR10 patient_phone
        DATE appointment_date
        TIME appointment_time
        VARCHAR500 reason
        ENUM status
        TIMESTAMP created_at
        VARCHAR40 slot_key UK
    }
    ADMINS {
        INT_UNSIGNED admin_id PK
        VARCHAR50 username UK
        VARCHAR255 password_hash
        TIMESTAMP created_at
    }
```

**Relationship:** one doctor can have many appointments (1:N); every appointment belongs to exactly one doctor.
`ADMINS` is a standalone table used only for administrator login and has no relationship to the other tables.
