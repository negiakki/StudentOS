# StudentOS — System Architecture

**Version:** 1.0 (Final)

**Architecture:** Modular Monolith

**Status:** Approved

---

# 1. Architecture Philosophy

StudentOS is built around one simple idea:

> **Coco is the brain. Everything else is a tool.**

Coco understands what the student wants.

The tools perform the work.

Python performs the calculations.

The AI explains the results.

The AI never guesses.

---

# 2. High-Level Architecture

```text
                   Student

                      │

          Next.js Frontend (PWA)

                      │

              REST API (FastAPI)

                      │

                 Coco Agent

          (Intent + Tool Selection)

                      │

     ┌──────────┬──────────┬──────────┐
     │          │          │          │
Attendance  Timetable  Assignment  Todo
   Tool        Tool        Tool     Tool
     │          │          │          │
     └──────────┴──────────┴──────────┘

                Business Services

                      │

               Repository Layer

                      │

          PostgreSQL (Supabase)

                      │

             Supabase Storage

                      │

             AI Provider Layer

        Gemini / IBM watsonx
```

---

# 3. Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Zustand
* TanStack Query
* Framer Motion

---

## Backend

* FastAPI
* Python
* SQLAlchemy
* Pydantic

---

## Database

* PostgreSQL (Supabase)

---

## Authentication

* Supabase Auth

Providers

* Google Login
* Email Login


Authentication Flow

Landing Page

↓

Google Login

OR

Email + Password

↓

Supabase Auth

↓

JWT

↓

FastAPI validates JWT

↓

Current User

↓

Business Services

↓

Database

---

## Storage

Supabase Storage

Stores

* Timetable PDFs
* Timetable Images

---

## Deployment

Frontend

* Vercel

Backend

* Render

Database

* Supabase

---

## AI

Primary

Gemini

Secondary

IBM watsonx

The AI provider can be changed without changing the rest of the application.

---

# 4. Project Structure

```text
studentos/

frontend/

backend/

docs/
```

---

## Frontend

```text
frontend/

app/

components/

features/

hooks/

lib/

services/

types/

styles/
```

Every feature has its own folder.

Example

Attendance

Timetable

Assignments

Todo

Dashboard

Chat

---

## Backend

```text
backend/

app/

api/

services/

repositories/

models/

schemas/

ai/

database/

core/

utils/
```

---

# 5. Coco Agent

Coco is the central intelligence layer.

Responsibilities

* Understand user requests.
* Decide which tool is needed.
* Call the tool.
* Collect the result.
* Ask the AI to explain it naturally.
* Return the response.

Coco never

* accesses the database directly
* performs calculations
* contains business logic

---

# 6. Tool Layer

Every feature is implemented as a tool.

Version 1 includes:

## Attendance Tool

Functions

* Get attendance
* Mark attendance
* Calculate attendance
* Calculate safe skips

---

## Timetable Tool

Functions

* Today's classes
* Weekly timetable
* Next class

---

## Assignment Tool

Functions

* Create
* Edit
* Delete
* Upcoming
* Overdue

---

## Todo Tool

Functions

* Create task
* Complete task
* Delete task
* Today's tasks

---

## Dashboard Tool

Functions

* Dashboard data
* Daily Brief context

---

## Weather Tool

Functions

* Current weather
* Forecast

---

## Notification Tool

Functions

* Attendance reminder
* Assignment reminder
* Daily Brief reminder

---

# 7. Business Services

Business Services contain all application logic.

Examples

Attendance Service

* Calculate percentage
* Calculate safe skips
* Update attendance

Timetable Service

* Parse timetable
* Edit timetable
* Generate weekly schedule

Assignment Service

Todo Service

Notification Service

Weather Service

Services never communicate directly with the AI.

---

# 8. Repository Layer

Repositories communicate with PostgreSQL.

Responsibilities

* Read data
* Save data
* Update data
* Delete data

Repositories never perform calculations.

---

# 9. Coco Request Flow

Example

Student asks

> Can I skip today's DBMS class?

Flow

```text
User

↓

Coco

↓

Attendance Tool

↓

Attendance Service

↓

Attendance Repository

↓

Database

↓

Structured Result

↓

Gemini

↓

Natural Response

↓

User
```

The AI only explains the structured result.

---

# 10. Dashboard Flow

```text
User opens StudentOS

↓

Dashboard Tool

↓

Attendance Service

Timetable Service

Assignment Service

Todo Service

Weather Service

↓

Dashboard Data

↓

Gemini

↓

Daily Brief

↓

Dashboard
```

---

# 11. Timetable Upload Flow

```text
Upload Image / PDF

↓

Supabase Storage

↓

FastAPI

↓

Gemini Vision

↓

Extract Subjects

↓

Extract Days

↓

Extract Timings

↓

Generate Preview

↓

User Confirms

↓

Database
```

If Coco is unsure, the user can edit the extracted timetable before saving.

---

# 12. Attendance Flow

During onboarding

Student enters

* Classes Attended
* Total Classes

After onboarding

Student opens Attendance page

↓

Calendar

↓

Select Date

↓

See classes for that day

↓

Present / Absent

↓

Save

↓

Attendance Service updates

* Attended Classes
* Total Classes
* Percentage
* Safe Skip Count

If notifications are enabled

Coco reminds the student in the evening.

Otherwise

Coco reminds the student on the next login.

Students can update attendance for previous dates at any time.

---

# 13. AI Provider Layer

Supported providers

* Gemini
* IBM watsonx

Future providers

* OpenAI
* Anthropic Claude

Changing providers should only require configuration changes.

---

# 14. Security

* JWT Authentication
* HTTPS
* Input Validation
* SQL Injection Protection
* Rate Limiting
* Secure File Uploads

---

# 15. Error Handling

If a tool fails

Only that feature fails.

The rest of StudentOS continues working.

Example

Weather unavailable

↓

Dashboard still loads.

Attendance still works.

Assignments still work.

---

If the AI provider fails

StudentOS continues functioning.

Users can still

* View dashboard
* Update attendance
* Manage assignments
* View timetable

The application displays:

> "Coco is temporarily unavailable. Your StudentOS data is still available."

---

# 16. Engineering Rules

1. Coco never accesses the database directly.
2. Every feature is implemented as a tool.
3. Business logic belongs in Services.
4. Database operations belong in Repositories.
5. Python performs all calculations.
6. The AI explains results—it never calculates them.
7. Every feature should reduce manual work.
8. Every workflow should be completable in under 30 seconds whenever possible.

---

# 17. Version 2 Extensions

The architecture supports adding new tools without major changes.

Future tools

* Academic Calendar Tool
* Assignment PDF Parser
* WhatsApp Parser
* Notes Tool
* Career Tool
* Internship Tool
* Resume Tool
* Voice Tool
* Avatar Tool

Each new feature becomes another tool that Coco can use.

No changes to the overall architecture are required.

---

# Final Principle

StudentOS is **not a chatbot with features**.

StudentOS is an application where **Coco is the intelligent interface**.

Students interact with Coco.

Coco interacts with the application.

The application interacts with the data.

This separation keeps the system accurate, scalable, and easy to maintain while allowing Coco to become more capable as new tools are added.
