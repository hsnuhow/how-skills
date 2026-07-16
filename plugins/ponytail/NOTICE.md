# Attribution

This plugin is derived from **ponytail** by DietrichGebert
(https://github.com/DietrichGebert/ponytail), licensed under MIT.

## Modifications in this build
- **Hooks removed.** The upstream project ships lifecycle hooks
  (SessionStart / SubagentStart / UserPromptSubmit) that auto-activate ponytail
  by default. This build includes **none** of them, so nothing runs
  automatically.
- **Main `ponytail` skill de-triggered.** Its frontmatter `description` was
  rewritten to be explicit-invoke only (the original "use on ANY coding task"
  broad auto-trigger was removed), so it never activates on ordinary coding —
  only when invoked by name.
- The command skills (`ponytail-review`, `-audit`, `-debt`, `-gain`, `-help`)
  are unchanged in behavior; they only run when explicitly invoked.

The original MIT license text is retained below where provided by upstream.
