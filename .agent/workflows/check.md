---
description: check
---

## Workflow: Full System Validation

Trigger: /check

Steps:
1. Type check: Run tsc --noEmit (TypeScript hatası var mı?)
2. Lint check: Run eslint . (Kod düzeni bozuk mu?)
3. Import check: Look for circular dependencies (Panel A imports B, B imports A?)
4. Test run: Run npm test (varsa testleri çalıştır)
5. Git status: Check for uncommitted changes
6. Dependency audit: Check if all imports resolve (dosyalar birbirini buluyor mu?)
7. Report findings:
   - "All systems green" veya
   - "Found X issues: [list]. Shall I fix them?"