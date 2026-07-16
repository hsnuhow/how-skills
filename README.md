# how-skills — personal Claude Code plugin marketplace

A single-repo [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
holding my personal skills as installable plugins, so they work on any machine.

## Plugins in this marketplace

| Plugin | What it adds | Invocation (namespaced) |
|--------|--------------|-------------------------|
| **skill-tools** | Skill-management commands | `/skill-tools:skill-list`, `/skill-tools:skill-status`, `/skill-tools:skill-RCM` |
| **ponytail** | Lazy-senior-dev / anti-over-engineering commands (commands-only, no hooks) | `/ponytail:ponytail`, `/ponytail:ponytail-review`, `/ponytail:ponytail-audit`, `/ponytail:ponytail-debt`, `/ponytail:ponytail-gain`, `/ponytail:ponytail-help` |

> Note: plugin skills are **namespaced** by plugin name, so `/skill-list` becomes
> `/skill-tools:skill-list` once installed as a plugin.

## Install on a new machine

```shell
# 1. Add this marketplace once
/plugin marketplace add hsnuhow/how-skills

# 2. Install the plugins you want
/plugin install skill-tools@how-skills
/plugin install ponytail@how-skills
```

To update later, push changes here, then on each machine:
```shell
/plugin marketplace update how-skills
```

## Plugin details

### skill-tools
- `skill-list` — list every available skill with a one-line Traditional Chinese
  purpose, in a concise bullet format (consistent across projects).
- `skill-status` — show which skills are enabled at system/user vs project vs
  plugin scope, and flag conflicts.
- `skill-RCM` — recommend skills worth installing for the current project, based
  on its memory, CLAUDE.md, product docs, and tech stack.

All three are **read-only** and **never write to memory**.

### ponytail
A **commands-only** build of [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)
(MIT). The original ships lifecycle hooks that auto-activate on every session;
**this build omits all hooks**, and the main `ponytail` skill is rewritten to be
**explicit-invoke only** — it stays dormant until you run `/ponytail:ponytail`
(or ask for it by name). See `plugins/ponytail/NOTICE.md` for attribution.

## Repo layout

```
.claude-plugin/marketplace.json     # catalog listing both plugins
plugins/
  skill-tools/
    .claude-plugin/plugin.json
    skills/{skill-list,skill-status,skill-RCM}/SKILL.md
  ponytail/
    .claude-plugin/plugin.json
    NOTICE.md
    skills/{ponytail,ponytail-audit,ponytail-debt,ponytail-gain,ponytail-help,ponytail-review}/SKILL.md
```
