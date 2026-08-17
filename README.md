# Agent Skills

Shared skills for coding agents. Clone once, install into Claude Code, Codex, Cursor, or any agent that reads a skills directory.

## Skills

- `council` — isolated multi-agent planning. Planners never share context; the host orchestrates.

## Install

From this checkout:

```sh
scripts/install-skills --list
scripts/install-skills
```

That symlinks `skills/council` into `~/.agents/skills/council`.

Claude Code / Cursor / Codex as well:

```sh
scripts/install-skills --all-homes
```

Selected skill, other target, copies instead of symlinks:

```sh
scripts/install-skills council
scripts/install-skills --target ~/.claude/skills
scripts/install-skills --mode copy --target ~/.agents/skills
scripts/install-skills --force council
scripts/install-skills --dry-run --all-homes
```

Symlinks are best for local development: edits in this checkout show up immediately.

## Layout

```text
skills/
  council/
    SKILL.md
    scripts/council
scripts/
  install-skills
```

Each skill is a directory with `SKILL.md`. Helpers live in that skill's `scripts/`.
