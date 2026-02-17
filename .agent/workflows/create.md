---
description: create
---

## Workflow: New Panel Creation

Trigger: /create

Steps:
1. Ask user: "Panel name? What should it display?"
2. Check PROJECT_CONTEXT_AI.md for naming conventions
3. Identify dependencies: Which existing panels will feed data to this?
4. Create scaffolding:
   - Create file: components/[PanelName].tsx
   - Create types: types/[panelname].ts
   - Create hook: hooks/use[PanelName].ts (if needed)
5. Boilerplate code with proper imports (check existing panels for style)
6. Add to PROJECT_CONTEXT_AI.md registry
7. Test: Does it compile? (tsc --noEmit)
8. Test: Does it render without crashing?
9. Commit: "feat: add [PanelName] panel"
10. Report: "Created [PanelName]. Connected to [X] data sources. Ready to use."