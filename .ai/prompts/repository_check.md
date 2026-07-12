# StudentOS Repository Integrity Check

Act as a senior software engineer performing a final repository sanity check.

Your goal is to verify that the repository is clean, internally consistent, and ready for commit.

Do not implement new features.

Do not refactor.

Do not optimize working code.

Only make changes if a genuine issue is found.

---

## Verify Repository Integrity

Check for:

### Code

- partially implemented features
- unfinished edits
- accidental code removal
- commented-out production code
- temporary debugging code
- console.log / print debugging left behind
- TODO/FIXME comments introduced during this task
- duplicate logic
- dead code
- unused variables
- unused imports
- broken imports
- broken exports
- circular imports

---

### Frontend

Verify:

- components compile correctly
- client/server component boundaries are correct
- no hydration issues introduced
- no obvious runtime errors
- consistent UI patterns

---

### Backend

Verify:

- endpoints remain consistent
- services match repositories
- schemas match API responses
- authentication/authorization unaffected
- no accidental database changes

---

### Integration

Verify:

- frontend and backend contracts still match
- request/response models remain consistent
- routes remain correct
- dashboard integration still works

---

### Repository

Verify:

- no unrelated files were modified
- no temporary files should be committed
- no merge artifacts
- no generated files accidentally added
- .gitignore is still respected

---

## Build & Verification

Confirm that:

- TypeScript passes
- production build succeeds
- backend imports succeed
- no obvious runtime regressions exist

Only perform verification appropriate for the modified files.

Do not run unnecessary full-project testing.

---

## Output

If everything is clean, respond only with:

✅ Repository integrity verified.

Repository is internally consistent.

No unintended changes detected.

Repository is safe to commit.

---

If an issue is found:

- classify it as Critical / Recommended / Optional
- implement only Critical issues
- explain why the issue matters
- summarize the fix
- verify the fix