---
description: /fix
---

## Workflow: Bug Fix Protocol

Trigger: /fix

Steps:
1. Read PROJECT_CONTEXT_AI.md to identify module
2. Run git status to check current state
3. If uncommitted changes exist: stash them or ask user
4. Create backup: cp [file] .backup/[file]_[timestamp].bak
5. Analyze impact: grep -r "import.*[filename]" . --include="*.tsx" --include="*.ts"
6. Show user: "I will modify [file]. This affects [X] other panels. Continue?"
7. Apply fix (surgical edit, max 20 lines)
8. Validate: Check syntax with tsc --noEmit
9. Test: Run npm test if available, else manual render check
10. If fail: restore from backup, report failure
11. If success: git add [specific_file], git commit -m "fix: [description]", git push
12. Report: "Fixed [file]. Tested. Committed. Other panels [affected/unaffected]."