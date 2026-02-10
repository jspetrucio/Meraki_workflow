---
paths: **/*
---

# Bug Memory - Auto-Check Rule

## CRITICAL: Known Issues Database

**BEFORE investigating ANY error, bug, or issue reported by the user, you MUST:**

1. Read `docs/ISSUES-FIXED/issue-fixed.md` FIRST
2. Check the "Quick Lookup by Error Message" table for matching fragments
3. If the error matches a known issue, tell the user it's already documented and what the fix was
4. Only investigate further if the error is NOT in the known issues database

## Trigger Words (check bug memory when user says):

- "erro" / "error"
- "nao funciona" / "nao funcionou" / "not working"
- "bug" / "crash" / "falha" / "failure"
- "troubleshooting" / "debug"
- "teste deu erro" / "test failed"
- "quebrou" / "broke"
- "404" / "500" / "AttributeError" / "TypeError"

## After Fixing a NEW Bug:

Always append the new issue to `docs/ISSUES-FIXED/issue-fixed.md` following the format:
```
## IF-NNN | Brief title

- **Symptom:** What the user saw
- **Root Cause:** Why it happened
- **Fix:** What was changed
- **File:** Which file(s)
- **Date:** YYYY-MM-DD
```

Also update the "Quick Lookup by Error Message" table at the bottom.
