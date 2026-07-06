# StudentOS — Coco AI Agent Design (Final)

**Version:** 1.0

---

# Philosophy

Coco is not the AI model.

Coco is the application's intelligence layer.

The AI model generates language.

StudentOS provides the facts.

---

# Core Rule

> The AI never guesses application data.

Every answer must come from StudentOS tools.

---

# Request Flow

```text
User

↓

Coco

↓

Select Tool

↓

Business Service

↓

Repository

↓

Database

↓

Structured Result

↓

AI Provider

↓

Natural Response

↓

User
```

---

# Coco Responsibilities

* Understand user requests.
* Choose the correct tool.
* Receive structured data.
* Ask the AI provider to explain it naturally.
* Return the response.

Coco never:

* accesses the database directly
* performs calculations
* contains business logic

---

# Available Tools (Version 1)

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

* Create assignment
* Update assignment
* Delete assignment
* List assignments

---

## Todo Tool

Functions

* Create task
* Complete task
* Delete task
* List today's tasks

---

## Dashboard Tool

Functions

* Build dashboard
* Generate Daily Brief data

---

## Weather Tool

Functions

* Current weather
* Today's forecast

---

## Notification Tool

Functions

* Attendance reminders
* Assignment reminders
* Daily Brief reminders

---

# Tool Rules

Every tool:

* returns structured JSON
* performs no UI rendering
* performs no natural language generation

Example

```json
{
  "success": true,
  "data": {},
  "errors": null
}
```

---

# AI Provider

Version 1 supports:

Primary

* Gemini

Secondary

* IBM watsonx

The provider is replaceable without changing Coco.

---

# Example

User:

"Can I skip today's DBMS class?"

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

Repository

↓

Database

↓

{
  "percentage":80,
  "safe_skips":2
}

↓

Gemini

↓

"Yes, you can safely skip today's DBMS lecture. You'll still have two safe skips remaining."
```

---

# Failure Handling

If the AI provider is unavailable:

* Dashboard continues working.
* Attendance continues working.
* Timetable continues working.
* Assignments continue working.

Display:

> "Coco is temporarily unavailable. Your StudentOS data is still available."

---

# Engineering Rules

1. Coco is an orchestrator, not a chatbot.
2. Every feature is exposed as a tool.
3. Python performs calculations.
4. AI explains results.
5. AI never directly accesses the database.
6. Services contain business logic.
7. Repositories only read and write data.
8. Keep Coco simple and deterministic.
