# Agent Skills

Skills for AI coding agents. Follows the [Agent Skills](https://agentskills.io/) format.

[![skills.sh](https://skills.sh/b/pmdroid/skills)](https://skills.sh/pmdroid/skills)

## Skills

- `council` — isolated multi-agent planning. Planners never share context; the host orchestrates.
- `triage` — turn an incoming bug report into a verdict. A council of four seats verifies the claim, finds the cause, sizes the blast radius, and checks prior art. Builds on `council`.

## Install

```bash
npx skills add pmdroid/skills
```

Global (all your projects):

```bash
npx skills add pmdroid/skills -g
```

One skill, or list first:

```bash
npx skills add pmdroid/skills --skill council
npx skills add pmdroid/skills --list
```

`triage` calls the `council` script, so install both.

## Layout

```text
skills/
  council/
    SKILL.md
    scripts/council
  triage/
    SKILL.md
    SIGNALS.md
```

## License

MIT
