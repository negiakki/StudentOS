# StudentOS

Before making any changes:

1. Read PROJECT_STATUS.md.
2. Read only the documentation relevant to the current task.
3. Explain your implementation plan before coding if the change affects architecture.

---

## Development Workflow

For every task:

1. Understand the requirement.
2. Identify the relevant files.
3. Implement the feature.
4. Check for TypeScript errors.
5. Check for Python errors.
6. Fix linting issues.
7. Verify that the application builds successfully.
8. Test the feature manually.
9. Verify that existing functionality has not broken.
10. Update PROJECT_STATUS.md.
11. Summarize what changed.

Never mark a task as complete until all checks pass.

---

## Verification Checklist

Before considering any feature complete, verify:

### General

- No TypeScript errors
- No Python errors
- No console errors
- No failing builds
- No runtime exceptions
- No broken imports
- No unused code
- No duplicate code

### UI

- Every button works
- Every form submits correctly
- Every modal opens and closes
- Every dropdown works
- Every page is responsive
- Loading states exist
- Empty states exist
- Error states exist

### Authentication

- Google login works
- Email signup works
- Email login works
- Forgot password works
- Logout works
- Protected routes work
- Session persists after refresh

### Timetable

- Upload works
- Parsing works
- Preview works
- Manual edits work
- Saving works

### Attendance

- Attendance can be marked
- Previous days can be edited
- Attendance percentage updates correctly
- Safe skip calculation is correct
- Dashboard updates immediately

### Assignments

- Create works
- Edit works
- Delete works
- Complete works
- Due dates display correctly

### Todo

- Create task
- Complete task
- Delete task
- Dashboard updates

### Coco

- Side panel opens
- Messages send successfully
- Correct tool is selected
- AI responses display correctly
- Fallback message appears if AI is unavailable

### Dashboard

- Greeting displays
- Today's classes display
- Attendance summary loads
- Assignments load
- Todo loads
- Daily Brief loads
- Weather loads (if configured)

---

## Scope

Never add features outside the PRD.

If a requested feature is outside the MVP, ask for confirmation before implementing it.

---

## If Something Doesn't Work

Never ignore an error.

Investigate the root cause.

Fix it before continuing.

Do not leave TODOs unless explicitly instructed.

---

## Final Rule

Do not say "Done" unless:

- The project builds successfully.
- The feature works.
- Existing functionality still works.
- The verification checklist passes.