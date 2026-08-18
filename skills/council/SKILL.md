---
name: council
description: Isolated multi-agent planning. Planners never share context; you broker information and synthesize. Use when the user wants a council, independent second opinions, multi-model planning, or an A-vs-B decision.
---

# Council

You are the orchestrator. Independent planners never see each other. You are the only one who reads every reply and decides what each planner learns next.

Do not simulate a council in one transcript. Run the helper.

## Skill path

Set once, then use `"$COUNCIL"`:

```bash
export COUNCIL="${COUNCIL:-$HOME/.agents/skills/council/scripts/council}"
```

Same script if installed under `~/.claude/skills`, `~/.cursor/skills`, `~/.codex/skills`, or this checkout: `skills/council/scripts/council`.

## Panel

Seats are roles, not models. Use **two different healthy engines**. More than two is fine.

Before round 1:

```bash
"$COUNCIL" engines --probe
```

`present` means the binary is on PATH. `--probe` runs a one-line ping and prints `ok`, `auth`, `quota`, `bad-model`, `empty`, `error`, or `timeout`.

- Do not pass `--model` unless the user named one or probe proved that slug works. A hardcoded slug fails on logins that do not have it.
- If `ask` exits non-zero or prints `council: empty reply`, move that seat to the next healthy engine. Same prompt. Empty stdout is not a reply.
- When healthy, prefer distinct engines such as `grok`, `cursor`, `claude`, `codex`, or `opencode`.

`--model` overrides the engine's own default. Replies are saved under `~/.council/runs/` (or `$COUNCIL_HOME/runs`). Pass `--session NAME` or `COUNCIL_SESSION` to group a panel.

## Run

Prompt on stdin. One process, one planner, no shared state.

```bash
"$COUNCIL" ask --engine grok --session "$COUNCIL_SESSION" <<'EOF'
<isolated builder prompt>
EOF

"$COUNCIL" ask --engine cursor --session "$COUNCIL_SESSION" <<'EOF'
<isolated critic prompt>
EOF
```

Run the first round in parallel. Wait for both before reading either. If a seat fails, replace it before reading the other reply as a finished panel.

## Planner prompt

Give every planner this shape. Do not include another planner's output.

```text
You are <name>. <role>

Objective:
<user objective>

Constraints:
- ...

Repository: <cwd only if relevant; do not dump the tree>

Selected insights:
- <only claims you chose to share; omit this section in round 1>

Questions:
- <your follow-ups; omit in round 1>

Reply with:
- recommendation
- assumptions
- risks
- alternatives
- open questions
- confidence 0-100

Print those six sections to stdout. That print is the entire deliverable.
Do not use tools, subagents, or plan-mode file writers.
Do not inspect the repository unless Repository: says to.
No chain-of-thought. No hidden reasoning.
```

## Invariants

1. Planner A cannot see planner B's reply.
2. Planner B cannot see planner A's reply.
3. Planners never see your notes or the full council state.
4. Everything that moves between planners goes through you.
5. You decide the exact prompt each planner gets.
6. Round 1 is blind: same objective, no selected insights, no questions.

Share **claims, questions, observations** — not transcripts. Never forward `Planner A said: "..."`.

## Loop

1. Probe engines. Blind round: all planners, identical objective, nothing from each other.
2. Compare: agreement, disagreement, missing information.
3. If needed, share selected insights and/or ask a follow-up. Still isolated.
4. Stop after 3 planner rounds, or sooner when you can decide.
5. Synthesize. Return only the synthesis unless the user asked for verbose.

## Synthesis

```text
Decision
========
<recommended approach>

Why
===
<key reasoning>

Agreement
=========
<where planners agreed>

Disagreements
=============
<important disagreements>

Risks
=====
<remaining risks>

Alternatives
============
<important alternatives>

Confidence
==========
<0-100>

Next Steps
==========
<concrete implementation steps>
```
