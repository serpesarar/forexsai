---
description: supabase
---

## Workflow: Database Check

Trigger: /dbcheck

Steps:
1. Check Supabase connection status
2. Validate: Are the tables described in PROJECT_CONTEXT_AI.md actually existing?
3. Check: Do panel queries match database schema?
4. Report: "DB Connection: OK/Failed. Mismatches found: [list]"