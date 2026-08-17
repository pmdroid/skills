# Agent Skills

Skills for AI coding agents. Follows the [Agent Skills](https://agentskills.io/) format.

[![skills.sh](https://skills.sh/b/pmdroid/skills)](https://skills.sh/pmdroid/skills)

## Skills

- `council` — isolated multi-agent planning. Planners never share context; the host orchestrates.

## Install

```bash
npx skills add pmdroid/skills
```

Global (all your projects):

```bash
npx skills add pmdroid/skills -g
```

Just council, or list first:

```bash
npx skills add pmdroid/skills --skill council
npx skills add pmdroid/skills --list
```

## Layout

```text
skills/
  council/
    SKILL.md
    scripts/council
```

## License

MIT
