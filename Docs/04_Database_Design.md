# StudentOS — Database Design

**Version:** 2.0 (Final)

**Database:** PostgreSQL (Supabase)

**ORM:** SQLAlchemy

**Status:** Final (Version 1)

---

# 1. Database Philosophy

StudentOS stores **facts**, not calculations.

The backend calculates:

* Attendance Percentage
* Safe Skip Count
* Attendance Predictions
* Daily Brief
* Dashboard Summary

The database stores only raw academic data.

---

# 2. Authentication

Authentication is fully managed by **Supabase Auth**.

Supabase handles:

* Email & Password Authentication
* Google Authentication
* Password Hashing
* Email Verification
* Forgot Password
* Sessions
* JWT Tokens

StudentOS only stores profile information.

Passwords are **never** stored inside the StudentOS database.

---

# 3. Entity Relationship Diagram

```text
User
│
├── Subjects (1:N)
│      │
│      ├── Timetable Slots (1:N)
│      ├── Attendance Summary (1:1)
│      └── Attendance Records (1:N)
│
├── Assignments (1:N)
│
├── Todos (1:N)
│
├── Uploaded Files (1:N)
│
├── Notifications (1:N)
│
├── Chat Messages (1:N)
│
└── Settings (1:1)
```

---

# 4. users

Stores StudentOS profile information.

| Column               | Type                                 |
| -------------------- | ------------------------------------ |
| id                   | UUID (Same as Supabase Auth User ID) |
| email                | TEXT                                 |
| full_name            | TEXT                                 |
| college              | TEXT                                 |
| degree               | TEXT                                 |
| onboarding_completed | BOOLEAN                              |
| created_at           | TIMESTAMP                            |
| updated_at           | TIMESTAMP                            |

---

# 5. subjects

Each subject belongs to one user.

| Column     | Type      |
| ---------- | --------- |
| id         | UUID      |
| user_id    | UUID      |
| name       | TEXT      |
| faculty    | TEXT NULL |
| classroom  | TEXT NULL |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

Examples

* DBMS
* Operating Systems
* Artificial Intelligence

---

# 6. timetable_slots

Each row represents one scheduled lecture.

| Column      | Type          |
| ----------- | ------------- |
| id          | UUID          |
| subject_id  | UUID          |
| day_of_week | INTEGER (1-7) |
| start_time  | TIME          |
| end_time    | TIME          |
| room        | TEXT NULL     |
| created_at  | TIMESTAMP     |
| updated_at  | TIMESTAMP     |

Example

Monday

09:00 → 10:00

DBMS

---

# 7. attendance_summary

Stores the latest attendance totals for each subject.

| Column           | Type      |
| ---------------- | --------- |
| id               | UUID      |
| subject_id       | UUID      |
| attended_classes | INTEGER   |
| total_classes    | INTEGER   |
| updated_at       | TIMESTAMP |

Purpose

Fast dashboard loading.

Attendance percentage is **never stored**.

Safe skips are **never stored**.

Everything is calculated when required.

---

# 8. attendance_records

Stores attendance history.

One row = one subject on one date.

| Column          | Type                  |
| --------------- | --------------------- |
| id              | UUID                  |
| subject_id      | UUID                  |
| attendance_date | DATE                  |
| status          | ENUM(PRESENT, ABSENT) |
| marked_at       | TIMESTAMP             |
| created_at      | TIMESTAMP             |

Purpose

* Calendar View
* Previous Attendance Editing
* Attendance Timeline

Whenever a record changes,

attendance_summary is automatically updated.

---

# 9. assignments

| Column      | Type                     |
| ----------- | ------------------------ |
| id          | UUID                     |
| user_id     | UUID                     |
| subject_id  | UUID NULL                |
| title       | TEXT                     |
| description | TEXT                     |
| due_date    | DATE                     |
| priority    | ENUM(LOW, MEDIUM, HIGH)  |
| status      | ENUM(PENDING, COMPLETED) |
| created_at  | TIMESTAMP                |
| updated_at  | TIMESTAMP                |

Subject is optional.

---

# 10. todos

| Column     | Type                    |
| ---------- | ----------------------- |
| id         | UUID                    |
| user_id    | UUID                    |
| title      | TEXT                    |
| completed  | BOOLEAN                 |
| due_date   | DATE NULL               |
| priority   | ENUM(LOW, MEDIUM, HIGH) |
| created_at | TIMESTAMP               |
| updated_at | TIMESTAMP               |

---

# 11. uploaded_files

Version 1 stores only the timetable.

Only one timetable exists per user.

Uploading a new timetable replaces the previous one.

| Column             | Type                                       |
| ------------------ | ------------------------------------------ |
| id                 | UUID                                       |
| user_id            | UUID                                       |
| file_category      | ENUM(TIMETABLE)                            |
| filename           | TEXT                                       |
| storage_path       | TEXT                                       |
| mime_type          | TEXT                                       |
| parsing_status     | ENUM(PENDING, PROCESSING, SUCCESS, FAILED) |
| parsing_confidence | DECIMAL                                    |
| uploaded_at        | TIMESTAMP                                  |

Actual files are stored in Supabase Storage.

---

# 12. notifications

| Column            | Type           |
| ----------------- | -------------- |
| id                | UUID           |
| user_id           | UUID           |
| title             | TEXT           |
| body              | TEXT           |
| notification_type | TEXT           |
| scheduled_for     | TIMESTAMP      |
| delivered_at      | TIMESTAMP NULL |
| sent              | BOOLEAN        |
| created_at        | TIMESTAMP      |

Examples

* Attendance Reminder
* Assignment Reminder
* Daily Brief Reminder

---

# 13. chat_messages

Stores conversations with Coco.

| Column          | Type             |
| --------------- | ---------------- |
| id              | UUID             |
| user_id         | UUID             |
| role            | ENUM(USER, COCO) |
| conversation_id | UUID             |
| message         | TEXT             |
| created_at      | TIMESTAMP        |

Conversation history improves context during the current semester.

---

# 14. settings

Stores user preferences.

| Column                | Type               |
| --------------------- | ------------------ |
| id                    | UUID               |
| user_id               | UUID               |
| dark_mode             | BOOLEAN            |
| notifications_enabled | BOOLEAN            |
| reminder_time         | TIME               |
| attendance_threshold  | INTEGER DEFAULT 75 |
| preferred_ai_provider | TEXT               |
| created_at            | TIMESTAMP          |
| updated_at            | TIMESTAMP          |

---

# 15. Relationships

```text
User
├── Subjects
├── Assignments
├── Todos
├── Uploaded Files
├── Notifications
├── Chat Messages
└── Settings

Subject
├── Timetable Slots
├── Attendance Summary
└── Attendance Records
```

---

# 16. Delete Account Flow

Deleting an account permanently removes:

* User Profile
* Subjects
* Timetable
* Attendance Summary
* Attendance Records
* Assignments
* Todos
* Uploaded Timetable
* Notifications
* Chat History
* Settings

Finally,

the authentication account is deleted through Supabase Auth.

Deletion is irreversible.

---

# 17. Indexes

Create indexes on:

* user_id
* subject_id
* attendance_date
* due_date
* email
* created_at

---

# 18. Security Rules

* Passwords are never stored.
* Every request requires authentication.
* Every query is scoped to the authenticated user.
* User IDs are never accepted from the frontend.
* The authenticated user is derived from the validated Supabase JWT.
* Uploaded files belong only to the authenticated user.

---

# 19. Engineering Principles

1. Store facts, never calculations.
2. Authentication belongs to Supabase.
3. Business logic belongs in Services.
4. Database operations belong in Repositories.
5. Use UUIDs for every primary key.
6. Keep the schema normalized.
7. One table, one responsibility.
8. Current semester only.
9. One active timetable per user.
10. Design for simplicity before scale.
