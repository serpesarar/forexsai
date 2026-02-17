---
description: undo
---

## Workflow: Safe Rollback

Trigger: /undo

Steps:
1. Show last 3 commits: git log --oneline -3
2. Ask: "Which one to revert? (1/2/3)"
3. If backup exists in .backup/: restore from there (faster)
4. Else: git revert [commit_hash] --no-edit
5. Verify: Check if file restored correctly
6. Test: Does it work now?
7. Commit: "revert: undo changes to [file]"
8. Report: "Rolled back to [timestamp]. Current state: [working/broken]"